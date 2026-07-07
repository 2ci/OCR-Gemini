import os
import cv2
import numpy as np

def order_points(pts):
    """
    Sort the 4 input coordinate points in order: top-left, top-right, bottom-right, bottom-left
    """
    pts = pts.reshape(4, 2)
    rect = np.zeros((4, 2), dtype="float32")
    
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]   # Top-left point has the minimum sum
    rect[2] = pts[np.argmax(s)]   # Bottom-right point has the maximum sum
    
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]  # Top-right point has the minimum difference
    rect[3] = pts[np.argmax(diff)]  # Bottom-left point has the maximum difference
    
    return rect

def perspective_transform(image, pts):
    """
    [Straighten Image Horizontally] Execute perspective transform to pixel-level straighten and crop skewed paper
    """
    rect = order_points(pts)
    (tl, tr, br, bl) = rect

    # Calculate the new width after straightening
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    max_width = max(int(widthA), int(widthB))

    # Calculate the new height after straightening
    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    max_height = max(int(heightA), int(heightB))

    # Four corners of the destination horizontal canvas
    dst = np.array([
        [0, 0],
        [max_width - 1, 0],
        [max_width - 1, max_height - 1],
        [0, max_height - 1]
    ], dtype="float32")

    # Calculate the matrix and perform perspective warp
    M = cv2.getPerspectiveTransform(rect, dst)
    return cv2.warpPerspective(image, M, (max_width, max_height))

def find_paper_contour(img):
    """
    Find the edge coordinates of the paper
    """
    h, w = img.shape[:2]
    ratio = 500.0 / h
    resized = cv2.resize(img, (int(w * ratio), 500), interpolation=cv2.INTER_AREA)
    
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    # Morphological close operation to connect broken edges
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
    gray = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
    blur = cv2.bilateralFilter(gray, 11, 75, 75)
    
    edged = cv2.Canny(blur, 30, 120)
    edged = cv2.dilate(edged, kernel, iterations=1)

    contours, _ = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
    
    for c in contours:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:
            return (approx / ratio).astype(int)
            
    # Fallback: If no perfect quadrilateral is found, use the bounding rect of the largest object
    if len(contours) > 0:
        x, y, w_box, h_box = cv2.boundingRect(contours[0])
        fallback_pts = np.array([[[x, y]], [[x+w_box, y]], [[x+w_box, y+h_box]], [[x, y+h_box]]])
        return (fallback_pts / ratio).astype(int)
        
    return None

def enhance_image_ultra(img):
    """
    Core filter: [Enhance Contrast] + [Enhance Font Sharpness] + [Remove Noise] while preserving slight color
    """
    # 1. [Remove Noise] Bilateral filter smoothes minor particles and noise on the paper surface without blurring text edges
    denoised = cv2.bilateralFilter(img, 9, 65, 65)
    
    # 2. [Strongly Enhance Contrast / Bleach] Dynamic background estimation and matrix division method
    k_size = max(img.shape[0], img.shape[1]) // 20
    if k_size % 2 == 0: k_size += 1
    bg_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k_size, k_size))
    bg = cv2.morphologyEx(denoised, cv2.MORPH_DILATE, bg_kernel)
    bg = cv2.GaussianBlur(bg, (k_size, k_size), 0)
    
    # Core division: Directly brighten yellowed/dark shadow backgrounds to pure white, instantly widening contrast between text and background
    whitened = cv2.divide(denoised, bg, scale=255)
    
    # 3. Adaptive brightness and local contrast stretching (CLAHE)
    lab = cv2.cvtColor(whitened, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    # Forcefully truncate grayish impurity areas, directly normalizing regions with brightness above 210 to pure white
    l_float = l.astype(np.float32)
    l_stretched = np.clip((l_float - 15) * (255.0 / (210.0 - 15.0)), 0, 255).astype(np.uint8)
    
    clahe = cv2.createCLAHE(clipLimit=3.5, tileGridSize=(8, 8))
    l_final = clahe.apply(l_stretched)
    
    color_base = cv2.cvtColor(cv2.merge((l_final, a, b)), cv2.COLOR_LAB2BGR)
    
    # 4. [Enhance Font Sharpness] Unsharp Masking (USM)
    # Subtract using a Gaussian layer to create a razor-sharp gradient on the ink edges of the text
    gauss = cv2.GaussianBlur(color_base, (0, 0), 3)
    sharpened = cv2.addWeighted(color_base, 1.6, gauss, -0.6, 0)
    
    # 5. [Ultimate Clean Sweep] Eliminate remaining isolated tiny noises
    gray_res = cv2.cvtColor(sharpened, cv2.COLOR_BGR2GRAY)
    sharpened[gray_res > 225] = [255, 255, 255]
    
    return sharpened

def apply_camscanner_effect(input_folder, output_folder):
    valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        
    image_files = [f for f in os.listdir(input_folder) if f.lower().endswith(valid_extensions)]
    
    if not image_files:
        print(f"No photos found in '{input_folder}'.")
        return

    print(f"🚀 Starting advanced processing of {len(image_files)} draft photos...")

    for img_name in image_files:
        input_path = os.path.join(input_folder, img_name)
        output_path = os.path.join(output_folder, f"scanned_{img_name}")
        
        # Keep the base architecture unchanged, but read in color mode to support slight color filtering
        img = cv2.imread(input_path)
        if img is None:
            continue
            
        orig = img.copy()
        
        # 1. Edge detection
        paper_contour = find_paper_contour(img)
        
        # 2. Straighten image horizontally (Perspective correction)
        if paper_contour is not None:
            print(f"📸 Successfully captured edges, auto-flattening and rotating: {img_name}")
            warped = perspective_transform(orig, paper_contour)
        else:
            print(f"⚠️ Blurred edges, skipping crop and performing horizontal high-fidelity enhancement directly: {img_name}")
            warped = orig
            
        # 3. Core enhancement (denoising, sharpening, high contrast)
        final_output = enhance_image_ultra(warped)
        
        # Save the processed high-definition slight color document
        cv2.imwrite(output_path, final_output)
        print(f"✅ Successfully exported: scanned_{img_name}")

    print(f"\n🎉 All processing completed! Go check out the '{output_folder}' folder.")

if __name__ == "__main__":
    INPUT_DIR = "./drafts"
    OUTPUT_DIR = "./scanned_output"
    
    if not os.path.exists(INPUT_DIR):
        os.makedirs(INPUT_DIR)
        print(f"Folder '{INPUT_DIR}' has been created. Please place your handwritten draft photos inside before running.")
    else:
        apply_camscanner_effect(INPUT_DIR, OUTPUT_DIR)
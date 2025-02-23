#include <opencv2/core.hpp>
#include <opencv2/imgproc.hpp>
#include <opencv2/features2d.hpp>
#include <opencv2/highgui.hpp>

#include <windows.h>
#include <iostream>

using namespace cv;
using namespace std;

// Function to capture the screen
Mat captureScreen() {
    HWND hwnd = GetDesktopWindow();
    HDC hdcScreen = GetDC(hwnd);
    HDC hdcMemDC = CreateCompatibleDC(hdcScreen);

    int width = GetSystemMetrics(SM_CXSCREEN);
    int height = GetSystemMetrics(SM_CYSCREEN);

    HBITMAP hBitmap = CreateCompatibleBitmap(hdcScreen, width, height);
    SelectObject(hdcMemDC, hBitmap);

    BitBlt(hdcMemDC, 0, 0, width, height, hdcScreen, 0, 0, SRCCOPY);

    BITMAPINFOHEADER bi;
    bi.biSize = sizeof(BITMAPINFOHEADER);
    bi.biWidth = width;
    bi.biHeight = -height;
    bi.biPlanes = 1;
    bi.biBitCount = 24;
    bi.biCompression = BI_RGB;

    Mat mat(height, width, CV_8UC3);
    GetDIBits(hdcMemDC, hBitmap, 0, height, mat.data, (BITMAPINFO*)&bi, DIB_RGB_COLORS);

    DeleteObject(hBitmap);
    DeleteDC(hdcMemDC);
    ReleaseDC(hwnd, hdcScreen);

    return mat;
}

// Function to detect MSER regions and return bounding boxes
vector<pair<Point, Point>> detectMSERBoxes(const Mat& image, int x, int y) {
    Ptr<MSER> mser = MSER::create();
    mser->setDelta(5);
    mser->setMinArea(20);
    mser->setMaxArea(500);
    mser->setMaxVariation(0.25);
    mser->setMinDiversity(0.1);

    vector<vector<Point>> regions;
    vector<Rect> bboxes;
    vector<pair<Point, Point>> boxCoords;

    Mat gray;
    cvtColor(image, gray, COLOR_BGR2GRAY);
    mser->detectRegions(gray, regions, bboxes);

	for (const auto& box : bboxes) {
		Point topLeft(box.tl().x + x, box.tl().y + y);
		Point botRight(box.br().x + x, box.br().y + y);
        boxCoords.push_back({topLeft, botRight});
    }

    return boxCoords;
}

// Function to snap a point to the nearest bounding box within a given distance
Point snapToNearestBox(const vector<pair<Point, Point>>& boxes, Point p, int maxDist) {
    Point closestPoint = p;
    int minDist = maxDist;

    for (const auto& box : boxes) {
        Point center((box.first.x + box.second.x) / 2, (box.first.y + box.second.y) / 2);
        int dist = norm(p - center);
        
        if (dist < minDist) {
            minDist = dist;
            closestPoint = center;
        }
    }

    return closestPoint;
}

// Function to simulate a mouse click at a given point
void clickAt(Point p) {
    SetCursorPos(p.x, p.y);
    mouse_event(MOUSEEVENTF_LEFTDOWN, p.x, p.y, 0, 0);
    mouse_event(MOUSEEVENTF_LEFTUP, p.x, p.y, 0, 0);
	mouse_event(MOUSEEVENTF_LEFTDOWN, p.x, p.y, 0, 0);
    mouse_event(MOUSEEVENTF_LEFTUP, p.x, p.y, 0, 0);
}

HWND createTransparentWindow() {
    // Register the window class
    const char* className = "TransparentWindowClass";
    WNDCLASS wc = {};
    wc.lpfnWndProc = DefWindowProc; // Default window procedure
    wc.hInstance = GetModuleHandle(NULL);
    wc.lpszClassName = className;
    RegisterClass(&wc);

    // Create the window
    HWND hwnd = CreateWindowEx(
        WS_EX_LAYERED | WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_TRANSPARENT,  // Add WS_EX_TRANSPARENT for click-through behavior
        className,
        "Transparent Circle Window",
        WS_POPUP,  // No border or title bar
        0, 0, GetSystemMetrics(SM_CXSCREEN), GetSystemMetrics(SM_CYSCREEN),  // Full screen
        NULL,
        NULL,
        wc.hInstance,
        NULL
    );

    // Set the window transparency
    SetLayeredWindowAttributes(hwnd, RGB(0, 0, 0), 0, LWA_COLORKEY);

    // Show the window
    ShowWindow(hwnd, SW_SHOW);
    UpdateWindow(hwnd);

    return hwnd;
}


// Function to clear the window (make it fully transparent before drawing anything)
void clearWindow(HWND hwnd) {
    HDC hdc = GetDC(hwnd);
    // Fill the window with a transparent color
    RECT rect;
    GetClientRect(hwnd, &rect);
    FillRect(hdc, &rect, (HBRUSH)GetStockObject(BLACK_BRUSH));  // Use black brush for transparency
    ReleaseDC(hwnd, hdc);
}

// Function to draw a circle at a given point
void drawCircle(HWND hwnd, Point p) {
    HDC hdc = GetDC(hwnd);
    HBRUSH hBrush = CreateSolidBrush(RGB(255, 0, 0));  // Red color
    SelectObject(hdc, hBrush);

    // Draw a circle at the specified position
    Ellipse(hdc, p.x - 10, p.y - 10, p.x + 10, p.y + 10);

    DeleteObject(hBrush);
    ReleaseDC(hwnd, hdc);
}

// Window procedure to handle the mouse click and keep the window unclickable
LRESULT CALLBACK WndProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    if (msg == WM_NCHITTEST) {
        return HTTRANSPARENT;  // Make the window unclickable
    }
    return DefWindowProc(hwnd, msg, wParam, lParam);
}

void drawBoxes(Mat& image, const vector<pair<Point, Point>>& boxes) {
    for (const auto& box : boxes) {
        rectangle(image, box.first, box.second, Scalar(0, 255, 0), 2); // Draw bounding box (green)
    }
}


int main() {
    HWND hwnd = createTransparentWindow();  // Create transparent window

    bool captureFrame = true;
    Mat screen;
    vector<pair<Point, Point>> boxes;
    POINT cursorPos;

    while (true) {
        GetCursorPos(&cursorPos);
		//cout << cursorPos.x << " " << cursorPos.y;
        Point mousePos(cursorPos.x, cursorPos.y);
		
        if (captureFrame) {
            screen = captureScreen();
			
			int boxSize = 200;
			
			// Calculate the top-left corner of the box (make sure it's within bounds)
			int x = max(mousePos.x - boxSize / 2, 0);  // Ensure the x-coordinate stays within bounds
			int y = max(mousePos.y - boxSize / 2, 0);  // Ensure the y-coordinate stays within bounds

			// Make sure the crop size doesn't go beyond the image boundaries
			int width = min(boxSize, screen.cols - x);  // Crop width
			int height = min(boxSize, screen.rows - y);  // Crop height

			// Define the ROI (Region of Interest)
			Rect roi(x, y, width, height);

			// Crop the image to the ROI
			Mat croppedImage = screen(roi);

            boxes = detectMSERBoxes(croppedImage, x, y);
			
        } else {
            Point shadowCursor = snapToNearestBox(boxes, mousePos, 100);
            clearWindow(hwnd);  // Clear the window before drawing the new circle
            drawCircle(hwnd, shadowCursor);  // Draw circle at the position of the nearest bounding box
        }

        captureFrame = !captureFrame;

        if (GetAsyncKeyState(VK_LBUTTON) & 0x8000) {
            clickAt(snapToNearestBox(boxes, mousePos, 100));
        }

        if (GetAsyncKeyState(VK_ESCAPE) & 0x8000) {
            break;
        }

        // Handle messages for the window
        MSG msg;
        if (PeekMessage(&msg, hwnd, 0, 0, PM_REMOVE)) {
            TranslateMessage(&msg);
            DispatchMessage(&msg);
        }
    }

    return 0;
}

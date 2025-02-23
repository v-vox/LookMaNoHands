#include <opencv2/core.hpp>
#include <opencv2/imgproc.hpp>
#include <opencv2/features2d.hpp>
#include <opencv2/highgui.hpp>

#include <thread>
#include <chrono>

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
    mser->setDelta(4);
    mser->setMinArea(15);
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
}

int main() {
    Mat screen;
    vector<pair<Point, Point>> boxes;
    POINT cursorPos;

	GetCursorPos(&cursorPos);
	//cout << cursorPos.x << " " << cursorPos.y;
	Point mousePos(cursorPos.x, cursorPos.y);

	screen = captureScreen();
	
	int boxSize = 200;
	
	int x = max(mousePos.x - boxSize / 2, 0);  // Ensure the x-coordinate stays within bounds
	int y = max(mousePos.y - boxSize / 2, 0);  // Ensure the y-coordinate stays within bounds
	int width = min(boxSize, screen.cols - x);  // Crop width
	int height = min(boxSize, screen.rows - y);  // Crop height

	Rect roi(x, y, width, height);

	Mat croppedImage = screen(roi);

	boxes = detectMSERBoxes(croppedImage, x, y);
		
	clickAt(snapToNearestBox(boxes, mousePos, 100));
    return 0;
}

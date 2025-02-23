CXX := g++
CXXFLAGS := -I"C:/msys64/mingw64/include/opencv4"
LDFLAGS := -L"C:/msys64/mingw64/lib/opencv4" -lopencv_core -lopencv_highgui -lopencv_imgproc -lgdi32 -lopencv_imgcodecs -lopencv_features2d

all: b.exe a.exe

b.exe: clickonce.cpp
	$(CXX) $< -o $@ $(CXXFLAGS) $(LDFLAGS)

a.exe: screencapture.cpp
	$(CXX) $< -o $@ $(CXXFLAGS) $(LDFLAGS)

clean:
	rm -f a.exe b.exe

#include <windows.h>

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    wchar_t dir[MAX_PATH], py[MAX_PATH];
    GetModuleFileNameW(NULL, dir, MAX_PATH);
    wchar_t *sl = wcsrchr(dir, L'\\');
    if (sl) *sl = 0;
    SetCurrentDirectoryW(dir);

    wsprintfW(py, L"%s\\runtime\\pythonw.exe", dir);
    if (GetFileAttributesW(py) == INVALID_FILE_ATTRIBUTES) {
        lstrcpyW(py, L"C:\\EccoBuild\\dreamcomp\\.venv\\Scripts\\pythonw.exe");
    }
    if (GetFileAttributesW(py) == INVALID_FILE_ATTRIBUTES) {
        wsprintfW(py, L"%s\\..\\dreamcomp\\.venv\\Scripts\\pythonw.exe", dir);
    }
    if (GetFileAttributesW(py) == INVALID_FILE_ATTRIBUTES) {
        lstrcpyW(py, L"pythonw.exe");
    }

    ShellExecuteW(NULL, L"open", py, L"launcher.py", dir, SW_HIDE);
    return 0;
}
#include <iostream>
#include <Windows.h>
#include <chrono>
#include <thread>

using namespace std;

int main() {


    cout << " 说明:按下“capslock”键以高速旋转，再次按下停止，该程序没有注入内存，不会封号 \n Written by BlingCc";

    while (true) {
        if (GetKeyState(VK_CAPITAL) & 1) {
            mouse_event(MOUSEEVENTF_MOVE, 800, 0, 0, 0);
        }

        this_thread::sleep_for(chrono::milliseconds(1));
    }

}

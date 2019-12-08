
#include <iostream>
#include <fstream>
#include <string>
#include <stdlib.h>

bool starts_with(const std::string& str, const std::string& sub) {
    return sub.length() <= str.length()
        && equal(sub.begin(), sub.end(), str.begin());
}

int main(int argc, char const *argv[]) {
    using namespace std;
    
    std::string cmd = "g++";
    
    for(int a = 1; a < argc; a++) {
        std::string arg = argv[a];
        if(starts_with(arg, "-std=")) {
            cmd.append(" ").append(arg);
        } else {
            cout << "unkownn arguments: " << arg << endl;
            return 1;
        }
    }
    
    
    ofstream of("test.cxx");
    for(;cin;) {
        std::string line;
        getline(cin, line);
        of << line << endl;
    }
    return system((cmd + " test.cxx -o test && ./test").c_str());
}

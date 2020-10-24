
#include <string>
#include <cxxabi.h>
#include <stdlib.h>

inline std::string demangle(char const *name) {
    int status;
    char * realname = abi::__cxa_demangle(name,0,0, &status);
    std::string realname_ = realname;
    free(realname);
    return realname_;    
}
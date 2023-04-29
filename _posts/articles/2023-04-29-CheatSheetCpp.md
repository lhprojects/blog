---
title: Cheat sheet of implicitly-declared constructor/ assignment operator in c++
tag: c++
---
# Cheat sheet of implicitly-declared constructor/ assignment operator in c++



```c++
class Class {
    
    // deleted if function can't be auto generated
    // otherwise, function is auto generated
    Class() = default;                                     // defaulted default constructor
    // or
    <No constructor declaration of any kind>               // implicitly-declared default constructor
    
    
        
    /* marked as deleted, if Class has
         user-declared move destructor
         user-declared move assignment operator
       as-if deprecated defaulted copy constructor, if Class has
         //user-declared copy constructor
         user-declared copy assignment operator
         user-declared user-defined destructor
       otherwise, as-if defaulted copy constructor
    */
    <No copy constructor declaration>                      // implicitly-declared copy constructor
    
    // deleted if function can't be auto generated
    // otherwise, function is auto generated
    Class(const Class &) = default;     // defaulted copy constructor

    
    
    /* marked as deleted, if Class has
         user-declared move destructor
         user-declared move assignment operator
       as-if deprecated defaulted copy constructor, if Class has
         user-declared copy constructor
         //user-declared copy assignment operator
         user-declared user-defined destructor
       otherwise, as-if defaulted copy assignment operator
    */
    <No copy assignment operator declaration>              // implicitly-declared copy assignment operator
        
        
        
    // deleted if function can't be auto generated
    // otherwise, function is auto generated
    Class& operator=(const Class &) = default;             // defaulted copy assignment operator

    /* marked as deleted, if Class has
         user-declared copy constructor
         user-declared copy assignment operator
         // user-declared move destructor
         user-declared move assignment operator
         user-declared user-defined destructor
       otherwise, as-if defaulted move constructor
    */
    <No move constructor declaration>                      // implicitly-declared move constructor
    
    // deleted if function can't be auto generated
    // otherwise, function is auto generated
    Class(Class &&) = default;                             // defaulted move constructor
    
    
    
    
    /* marked as deleted, if Class has
         user-declared copy constructor
         user-declared copy assignment operator
         user-declared move destructor
         //user-declared move assignment operator
         user-declared user-defined destructor
       otherwise, as-if defaulted move assignment operator
    */
    <No move assignment operator declaration>              // implicitly-declared move constructor
        
    // deleted if function can't be auto generated
    // otherwise, function is auto generated
    Class& operator=(Class &&) = default;                  // defaulted copy assignment operator
    
    
    
    // deleted if function can't be auto generated
    // otherwise, function is auto generated
    ~Class() = default;                                    // defaulted default constructor
    // or
    <No destructor declaration>                            // implicitly-declared default constructor
}
```



# Rules of thumb

## Rule of three

If a  class defines any of the following then it should probably explicitly define all three:

* destructor
* copy constructor
* copy assignment operator

## Rule of five

If a  class defines any of the following then it should probably explicitly define all five:

* destructor
* copy constructor
* copy assignment operator
* move constructor
* move assignment operator

Extreme case: if you can't afford the cost of copy constructor/copy assignment operator, just delete them. 


using namespace std;
#ifndef STACK_H
#define STACK_H
#include <iostream>

template <typename T>

class Stack {
    private:
        T* Array;
        int top;
        int capacity;


    public:
    
    Stack(int size) {
        Array = new T[size];
        capacity = size;
        top = -1;
    }

    void push(T element) {
        if (top == capacity - 1) {
            cout << "Stack overflow" << endl;
            return;
        }
        Array[++top] = element;
    }

    T pop() {
        if (top == -1) {
            cout << "Esta vacio el stack" << endl;
            return T(); 
        }
        return Array[top--];
    }

    T peek() {
        if (top == -1) {
            cout << "Esta vacio el stack" << endl;
            return T();
        }
        return Array[top];
    }

    bool isEmpty() {
        return top == -1;
    }

    int size() {
        return top + 1;
    }

};

#endif





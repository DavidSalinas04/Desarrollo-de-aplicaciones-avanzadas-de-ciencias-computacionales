#include <iostream>
using namespace std;
#ifndef QUEUE_H
#define QUEUE_H

template <typename T>

class Queue {
    private:

        T* Array;
        int head;
        int tail;
        int capacity;
        int Size;

    public:

        Queue(int max){
            capacity = max;
            head = 0;
            tail = 0;
            Array = new T[max];
            Size = 0;
        }

        void enqueue(T element){
            if (Size == capacity) {
                cout << "Queue llena" << endl;
                return;
            }
            Array[tail] = element;
            tail = (tail + 1) % capacity;
            Size++;
        }

        T dequeue(){
            if (Size == 0) {
                cout << "Queue vacia" << endl;
                return T(); 
            }
            T element = Array[head];
            head = (head + 1) % capacity;
            Size--;
            return element;
        }

        T front(){
            return Array[head];
        }

        bool isEmpty(){
            return head == tail;
        }

        int size(){
            return Size;
        }

        void clear(){
            head = 0;
            tail = 0;
            Size = 0;
        }
};


#endif

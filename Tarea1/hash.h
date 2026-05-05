#include <iostream>
using namespace std;
#ifndef HASH_H
#define HASH_H

template <typename K, typename V>

class Hash {
    private:
        K* keys;
        V* values;
        int capacity;
        int size;

    public:
        Hash(int max) {
            capacity = max;
            size = 0;
            keys = new K[max];
            values = new V[max];
        }

        void insert(K key, V value) {
            if (size == capacity) {
                cout << "Hash lleno" << endl;
                return;
            }
            keys[size] = key;
            values[size] = value;
            size++;
        }

        V search(K key) {
            for (int i = 0; i < size; i++) {
                if (keys[i] == key) {
                    return values[i];
                }
            }
            cout << "Clave no encontrada" << endl;
            return V();
        }

        void remove(K key) {
            for (int i = 0; i < size; i++) {
                if (keys[i] == key) {
                    for (int j = i; j < size - 1; j++) {
                        keys[j] = keys[j + 1];
                        values[j] = values[j + 1];
                    }
                    size--;
                    return;
                }
            }
            cout << "Clave no encontrada" << endl;
        }

        bool isEmpty() {
            return size == 0;
        }

        int getSize() {
            return size;
        }

};

#endif

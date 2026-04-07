#include "stack.h"
#include "queue.h"
#include "hash.h"
using namespace std;
#include <iostream>

template class Stack<int>;
template class Queue<int>;
template class Hash<string, int>;

int main() {

    Stack<int> intStack(10);

    intStack.push(1);
    intStack.push(2);
    intStack.push(3);

    cout << "Top del stack: " << intStack.peek() << endl;
    cout << "Tamano del stack: " << intStack.size() << endl;
    cout << "Pop del stack: " << intStack.pop() << endl;
    cout << "Top del stack despues de pop: " << intStack.peek() << endl;
    cout << "El stack esta vacio ? " << (intStack.isEmpty() ? "Si" : "No") << endl;
    cout << "------------------------------------------------------------------- " << endl;

    Queue<int> intQueue(10);

    intQueue.enqueue(4);
    intQueue.enqueue(5);
    intQueue.enqueue(6);

    cout << "Front de la queue: " << intQueue.front() << endl;
    cout << "Tamano de la queue: " << intQueue.size() << endl;
    cout << "Dequeue de la queue: " << intQueue.dequeue() << endl;
    cout << "Front de la queue despues de dequeue: " << intQueue.front() << endl;
    cout << "La queue esta vacia ? " << (intQueue.isEmpty() ? "Si" : "No") << endl;
    cout << "------------------------------------------------------------------- " << endl;

    Hash<string, int> stringIntHash(10);

    stringIntHash.insert("Clave1", 7);
    stringIntHash.insert("Clave2", 8);
    stringIntHash.insert("Clave3", 9);

    cout << "Valor buscado: " << stringIntHash.search("Clave2") << endl;
    cout << "Tamano del hash: " << stringIntHash.getSize() << endl;
    stringIntHash.remove("Clave2");
    cout << "Valor buscado despues de eliminar: " << stringIntHash.search("Clave2") << endl;
    cout << "El hash esta vacio ? " << (stringIntHash.isEmpty() ? "Si" : "No") << endl;


    return 0;


}




import random
import multiprocessing
import time


luvut = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]

def childProcess(pipe):
    luku = random.choice(luvut)
    pipe.send(luku)
    pipe.close()

def parentProcess():
    childProcesses = []
    pipes = []
    for i in range(4):
        parent_pipe, child_pipe = multiprocessing.Pipe()
        child = multiprocessing.Process(target=childProcess, args=(child_pipe,))
        childProcesses.append(child)
        pipes.append(parent_pipe)
        child.start()
        
        

    for child, parent_pipe in zip(childProcesses, pipes):
        print(f"Käynnistetään lapsiprosessi {child.pid} ja odotetaan sitä")
        received_number = parent_pipe.recv()
        print(f"Lapsiprosessin valitsema luku on {received_number}")
        child.join()
        print(f"Lapsiprosessi {child.pid} päättynyt")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    parentProcess()
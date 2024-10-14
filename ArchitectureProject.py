import random
import multiprocessing
from multiprocessing import shared_memory
import numpy as np

def scheduler(share_memory_name, size):
    existing_shm = shared_memory.SharedMemory(name=share_memory_name)

    # Luetaan data
    data = np.ndarray((size,), dtype=np.int64, buffer=existing_shm.buf)

    # Tulostetaan luettavat arvot
    print("Lajiteltu lista:", sorted(data))

    existing_shm.close()

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
        
    # Luodaan yhteinen muisti
    shm = shared_memory.SharedMemory(create=True, size=4 * np.int64().nbytes)

    # Muuttuja, johon tallennetaan lapset
    shm_array = np.ndarray((4,), dtype=np.int64, buffer=shm.buf)

    for index, (child, parent_pipe) in enumerate(zip(childProcesses, pipes)):
        print(f"Käynnistetään lapsiprosessi {child.pid} ja odotetaan sitä")
        received_number = parent_pipe.recv()
        print(f"Lapsiprosessin valitsema luku on {received_number}")
        
        # Tallennetaan saatu luku yhteiseen muistiin
        shm_array[index] = received_number

        child.join()
        print(f"Lapsiprosessi {child.pid} päättynyt")

    # Käynnistetään scheduler
    scheduler(shm.name, 4)

    # Irrotetaan yhteinen muisti
    shm.close()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    parentProcess()
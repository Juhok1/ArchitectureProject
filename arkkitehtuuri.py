import random
import multiprocessing
from multiprocessing import shared_memory
import numpy as np

def scheduler(share_memory_name, size):
    existing_shm = shared_memory.SharedMemory(name=share_memory_name)

    # Read data
    data = np.ndarray((size,), dtype=np.int64, buffer=existing_shm.buf)

    # Print sorted list of numbers
    print("Lajiteltu lista:", sorted(data.tolist()))

    existing_shm.close()

# Predefined list of numbers
luvut = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]

def childProcess(pipe, luku):
    pipe.send(luku)
    pipe.close()

def parentProcess():
    childProcesses = []
    pipes = []
    
    # Ask the user for 4 numbers, or choose randomly if input is empty
    selected_numbers = []
    for i in range(4):
        user_input = input(f"Anna luku väliltä {min(luvut)}-{max(luvut)} (numero {i+1}/4)")
        
        # If the user presses Enter without input, pick a random number
        if user_input.strip() == "":
            number = random.choice(luvut)
        else:
            try:
                number = int(user_input)
                if number not in luvut:
                    number = random.choice(luvut)  # Default to random number if input is invalid
            except ValueError:
                number = random.choice(luvut)  # Default to random number if input is not an integer
        
        selected_numbers.append(number)

    # Create shared memory
    shm = shared_memory.SharedMemory(create=True, size=4 * np.int64().nbytes)

    # Array to store the numbers in shared memory
    shm_array = np.ndarray((4,), dtype=np.int64, buffer=shm.buf)

    # Spawn child processes
    for i in range(4):
        parent_pipe, child_pipe = multiprocessing.Pipe()
        child = multiprocessing.Process(target=childProcess, args=(child_pipe, selected_numbers[i]))
        childProcesses.append(child)
        pipes.append(parent_pipe)
        child.start()

    for index, (child, parent_pipe) in enumerate(zip(childProcesses, pipes)):
        print(f"Käynnistetään lapsiprosessi {child.pid} ja odotetaan sitä")
        received_number = parent_pipe.recv()
        print(f"Lapsiprosessin valitsema luku on {received_number}")
        
        # Store received number in shared memory
        shm_array[index] = received_number

        child.join()
        print(f"Lapsiprosessi {child.pid} päättynyt")

    # Run the scheduler
    scheduler(shm.name, 4)

    # Unlink shared memory
    shm.unlink()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    parentProcess()

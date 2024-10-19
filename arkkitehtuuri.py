import os
import random
import numpy as np
import sys
from multiprocessing import shared_memory

# Lapsiprosessi, joka lähettää viestiputken kautta numeron init-prosessille
def childProcess(pipe, selected_number):
    pipe.send(selected_number)
    pipe.close()

# Init-prosessi (pääprosessi)
def parentProcess():
    child_pids = []
    pipes = []
    selected_numbers = []
    
    # Generoi satunnaiset numerot lapsiprosesseille (0-19)
    for i in range(4):
        number = random.randint(0, 19)
        selected_numbers.append(number)

    print(f"Generoidut numerot: {selected_numbers}")

    # Viestiputket (pipes) lapsiprosessien ja initin välille
    for i in range(4):
        parent_pipe, child_pipe = os.pipe()  # Luo viestiputki
        pid = os.fork()  # Forkataan uusi prosessi

        if pid == 0:  # Lapsiprosessi
            os.close(parent_pipe)  # Lapsi ei tarvitse parent-päätä putkesta
            child_pipe = os.fdopen(child_pipe, 'w')  # Avataan kirjoitus-moodi
            childProcess(child_pipe, selected_numbers[i])
            os._exit(0)  # Lapsiprosessi päättyy
        else:  # Init-prosessi
            os.close(child_pipe)  # Init ei tarvitse child-päätä putkesta
            pipes.append(parent_pipe)  # Tallennetaan parent-pipe
            child_pids.append(pid)  # Tallennetaan lapsiprosessin pid

    # Init lukee viestit lapsilta ja tallentaa ne jaettuun muistiin
    shm = shared_memory.SharedMemory(create=True, size=4 * np.int64().nbytes)
    shm_array = np.ndarray((4,), dtype=np.int64, buffer=shm.buf)

    for i, parent_pipe in enumerate(pipes):
        parent_pipe = os.fdopen(parent_pipe)  # Avataan lukumoodissa
        received_number = int(parent_pipe.read())  # Lue viesti putkesta
        print(f"Init sai numeron: {received_number} lapsiprosessilta {child_pids[i]}")
        shm_array[i] = received_number  # Tallenna jaettuun muistiin

    # Odotetaan lapsiprosessien päättymistä
    for pid in child_pids:
        os.waitpid(pid, 0)

    # Ajastimen käynnistys (scheduler)
    scheduler(shm.name, 4)

    # Jaetun muistin vapautus
    shm.close()
    shm.unlink()

# Scheduler-prosessi, joka lukee jaettuun muistiin tallennetut numerot ja lajittelee ne
def scheduler(share_memory_name, size):
    existing_shm = shared_memory.SharedMemory(name=share_memory_name)

    # Lue data jaetusta muistista
    data = np.ndarray((size,), dtype=np.int64, buffer=existing_shm.buf)
    
    # Lajittele ja tulosta lista
    sorted_data = sorted(data.tolist())
    print("Lajiteltu lista:", sorted_data)

    # Sulje jaettu muisti
    existing_shm.close()

if __name__ == "__main__":
    parentProcess()
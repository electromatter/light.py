'''
Copyright (c) 2016, Eric Chai <electromatter@gmail.com>
Copyright (c) 2016, Brian Van Rosendale <vanrosendalebrian@gmail.com>

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
'''

import time
import random
import array

#linear, crossectional, and volumetric size */
LINSIZE = 16 + 4
AREASIZE = LINSIZE*LINSIZE
VOLSIZE = LINSIZE*LINSIZE*LINSIZE

DX = 1
DY = LINSIZE
DZ = AREASIZE

# placeholder opaque light value for debugging
OPAQUE = -128
# benchmark sample size - 12.8s for 100000 on my machine with -O3
SAMPLESIZE = 10000

'''
arrays are packed: DX*x + DY*y + DZ*z

positive seeds emit light
negitive seeds consume light

the inner border is used to connect nehbors
the outer border is used as a terminal sentinal value (OPAQUE)

seed should have the border and whatever light source/impedance values
destination (dest) should be initialized to be all zeros

the queue should be able to hold atleast 6*VOLSIZE elements

light values take the max (they do not add!)
'''


def probe(index, value, seed, dest, seed_queue, end):
    '''
    index - index of seed and dest for the block being probed
    value - value incoming light value before seeds are evaluated
    seed - source array of seed for light values
    dest - destination array of calculated light values
    seed_queue, adds a new seed to the queue
    '''
    value = value + seed[index] if seed[index] < 0 else seed[index]

    if value <= dest[index]:
        return end
    if value == 0:
        print('{} {}'.format(index, value))
    #this value is higher, fill the block and enqueue it
    dest[index] = value
    seed_queue[end] = index
    return end + 1

def fill(index, seed, dest, seed_queue, end):
    '''
    returns int pointer

    int index
    seed - source array of seed for light values
    dest - destination array of calculated light values
    seed_queue - queue of light seeds
    '''
    value = dest[index]

    #probe in each direction
    end = probe(index + DX, value, seed, dest, seed_queue, end)
    end = probe(index + DY, value, seed, dest, seed_queue, end)
    end = probe(index + DZ, value, seed, dest, seed_queue, end)
    end = probe(index - DX, value, seed, dest, seed_queue, end)
    end = probe(index - DY, value, seed, dest, seed_queue, end)
    end = probe(index - DZ, value, seed, dest, seed_queue, end)
    return end

def scan_seed(seed, seed_queue, end):
    '''
    seed - chunk light data
    seed_queue - priority queue that ranks light sources

    enqueue all light sources
    '''
    # scan entire chunk for seeds
    for i in range(VOLSIZE):
        if seed[i] > 0:
            seed_queue[end] = i
            end += 1

    return end

def light(seed, dest, seed_queue, end):
    '''
    process the queue
    call scan_seed first to initialize the queue

    seed - source array of seed for light values
    dest - destination array of calculated light values
    seed_queue - queue of light seeds
    '''

    # pop an item off the queue and fill it
    i = 0
    while i < end:
        end = fill(seed_queue[i], seed, dest, seed_queue, end)
        i += 1

def light2(seed, dest):
    '''
    I don't think this is ever called so I'm not worrying about it

    seed - source array of seed for light values
    dest - destination array of calculated light values
    '''
    #seed_queue = queue.PriorityQueue()

    #seed_queue = scan_seed(seed, queue)
    #light(seed, dest, queue, seed_queue)


# BELOW HERE IS FOR DEBUGGING/BENCHMARKING

def print_chunk(dest):
    '''display the chuck in a readable format'''
    for i in range(LINSIZE):
        for j in range(LINSIZE):
            for k in range(LINSIZE):
                print('{:3d} '.format(dest[i * DZ + j * DY + k * DX]), end='')
            print()
        print('\n')

def border(seed):
    '''sets the edges of seed to be the OPAQUE value'''
    m = LINSIZE - 1

    for i in range(LINSIZE):
        for j in range(LINSIZE):
            seed[0*DZ + i*DY + j*DX] = OPAQUE
            seed[i*DZ + 0*DY + j*DX] = OPAQUE
            seed[i*DZ + j*DY + 0*DX] = OPAQUE
            seed[m*DZ + i*DY + j*DX] = OPAQUE
            seed[i*DZ + m*DY + j*DX] = OPAQUE
            seed[i*DZ + j*DY + m*DX] = OPAQUE
    return seed

def access(base, x, y, z):
    '''
    returns char *access

    char *base
    int x
    int y
    int z

    is this even used?

    reverse (index//DZ, (index%DZ)//DY, (index%DZ)%DY)
    '''
    assert(x >= 0 and x < LINSIZE)
    assert(y >= 0 and y < LINSIZE)
    assert(z >= 0 and z < LINSIZE)
    return base + x * DX + y * DY + z * DZ

def fill_rand(seed):
    '''
    returns void

    char *seed
    '''
    m = LINSIZE - 1
    value = 0

    for i in range(1, m):
        for j in range(1, m):
            for k in range(1, m):
                # generate a value
                value = random.randint(0, 65520)
                if (value < 1000):
                    value = random.randint(0, 15)
                elif (value < 20):
                    value = -2
                else:
                    value = -1

                # fill the block
                seed[i * DZ + j * DY + k * DX] = value
    return seed

def main():
    # setup the data structures to be used
    seed = array.array('i', [0]*VOLSIZE)
    dest = array.array('i', [0]*VOLSIZE)
    seed_queue = array.array('i', [0]*VOLSIZE*6)

    # setup by surrounding with opaque blocks and filling random light levels
    seed = border(seed)
    seed = fill_rand(seed)

    start_time = time.time()
    for i in range(SAMPLESIZE):
        for i in range(VOLSIZE):
            dest[i] = 0
        #dest = [0]*VOLSIZE  #may not be necessary, was memset in the c code
        light(seed, dest, seed_queue, scan_seed(seed, seed_queue, 0))
    end_time = time.time()
    elapsed = end_time - start_time     #may not be the same as the c code

    # show the chunk for debugging
    print_chunk(dest)

    print('{} loops in {}s ({} loops/sec)'.format(SAMPLESIZE, elapsed,
                                                  SAMPLESIZE / elapsed))

if __name__ == '__main__':
    main()
    main()

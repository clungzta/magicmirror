import json
import numpy as np

# def np_tofile(filepath, A):
#     """convert a numpy array to string"""
#     with open("file.dat","a+") as f:
#         np.save(outfile, x)

# def np_fromfile(filepath):
#     """convert string to numpy array"""
#     with open(filepath) as json_file:  
#         np.save(outfile, x)

if __name__ == "__main__":
    a = np.identity(3)
    np.save('identity.npy', a)

    b = np.load('identity.npy')

    print(b)
    print(a==b)

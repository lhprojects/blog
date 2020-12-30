
# don't remove the follows for your use
# Author: https://lhprojects.github.io/blog/
# don't remove above lines

import numba
import numpy as np


def unique(ar, return_counts = False, return_hit_accuracy = False):
    '''
    ar: integer array
    return:
        uniques [, uniques_counts] [, hit_accuracy]
        hit_accuracy should be close to 1. unless
        the hash function has some quality problem
    '''
    
    f,s,t = unique_impl(ar)
    if return_counts and return_hit_accuracy:
        return f, s, t
    elif return_counts:
        return f, s
    elif return_hit_accuracy:
        return f, t
    else:
        return f
    
def unique32(ar, return_counts = False, return_hit_accuracy = False):
    '''
    ar: integer array
    NOTE: upper 32 bits ignored for hash function
    return:
        uniques [, uniques_counts] [, hit_accuracy]
        hit_accuracy should be close to 1. unless
        the hash function has some quality problem
    '''
    
    f,s,t = unique_impl32(ar)
    if return_counts and return_hit_accuracy:
        return f, s, t
    elif return_counts:
        return f, s
    elif return_hit_accuracy:
        return f, t
    else:
        return f

@numba.njit
def length(l):
    # https://en.wikipedia.org/wiki/Fowler%E2%80%93Noll%E2%80%93Vo_hash_function
    l = int(np.ceil(np.log2(l)))
    # 4*len(ar) > l > 2*len(ar)
    l = 2 << l
    return l

@numba.njit
def FNV_1(v):
    
    byte_mask = np.uint64(255)
    bs = np.uint64(v)
    x1 = (bs) & byte_mask
    x2 = (bs>>8) &byte_mask
    x3 = (bs>>16) &byte_mask
    x4 = (bs>>24) &byte_mask
    x5= (bs>>32) &byte_mask
    x6= (bs>>40) &byte_mask
    x7= (bs>>48) &byte_mask
    x8= (bs>>56) &byte_mask

    FNV_primer = np.uint64(1099511628211)
    FNV_bias = np.uint64(14695981039346656037)
    h = FNV_bias
    h = h*FNV_primer
    h = h^x1
    h = h*FNV_primer
    h = h^x2
    h = h*FNV_primer
    h = h^x3
    h = h*FNV_primer
    h = h^x4
    h = h*FNV_primer
    h = h^x5
    h = h*FNV_primer
    h = h^x6
    h = h*FNV_primer
    h = h^x7
    h = h*FNV_primer
    h = h^x8
    return h

@numba.njit
def FNV_1_32(v):
    
    byte_mask = np.uint64(255)
    bs = np.uint64(v)
    x1 = (bs) & byte_mask
    x2 = (bs>>8) &byte_mask
    x3 = (bs>>16) &byte_mask
    x4 = (bs>>24) &byte_mask

    FNV_primer = np.uint64(1099511628211)
    FNV_bias = np.uint64(14695981039346656037)
    h = FNV_bias
    h = h*FNV_primer
    h = h^x1
    h = h*FNV_primer
    h = h^x2
    h = h*FNV_primer
    h = h^x3
    h = h*FNV_primer
    h = h^x4
    return h
    
@numba.njit
def unique_impl(ar):
    
    l = len(ar)
    l = int(np.ceil(np.log2(l)))
    # 4*len(ar) > l > 2*len(ar)
    l = 2 << l
    
    mask = l - 1 
    uniques = np.empty(l, dtype=ar.dtype)
    uniques_cnt = np.zeros(l, dtype=np.int_)
    
    total = 0    
    miss_hits = 0    
    
    for v in ar:
        h = FNV_1(v)
        
        index = (h & mask)
        
        # open address hash
        # great cache performance
        while True:
            if uniques_cnt[index] == 0:
                uniques_cnt[index] += 1
                uniques[index] = v
                total += 1
                break
            elif uniques[index] == v:
                uniques_cnt[index] += 1 
                break
            else:
                miss_hits += 1
                index += 1
                index = index & mask
    
    
    # flush the results in a concrete array
    uniques_ = np.empty(total, dtype=ar.dtype)
    uniques_cnt_ = np.empty(total, dtype=np.int_)
    t = 0
    for i in range(l):
        if uniques_cnt[i] > 0:
            uniques_[t] = uniques[i]
            uniques_cnt_[t] = uniques_cnt[i]
            t += 1
            
    if len(ar) == 0:
        hit_accuracy = np.nan
    else:
        hit_accuracy = len(ar)/((len(ar) + miss_hits)*1.0)
    return uniques_, uniques_cnt_, hit_accuracy

@numba.njit
def unique_impl32(ar):
    
    l = len(ar)
    l = int(np.ceil(np.log2(l)))
    # 4*len(ar) > l > 2*len(ar)
    l = 2 << l
    
    mask = l - 1      
    uniques = np.empty(l, dtype=ar.dtype)
    uniques_cnt = np.zeros(l, dtype=np.int_)
    
    total = 0    
    miss_hits = 0    
    
    for v in ar:
        h = FNV_1_32(v)
        
        index = (h & mask)
        
        # open address hash
        # great cache performance
        while True:
            if uniques_cnt[index] == 0:
                uniques_cnt[index] += 1
                uniques[index] = v
                total += 1
                break
            elif uniques[index] == v:
                uniques_cnt[index] += 1 
                break
            else:
                miss_hits += 1
                index += 1
                index = index & mask
    
    
    # flush the results in a concrete array
    uniques_ = np.empty(total, dtype=ar.dtype)
    uniques_cnt_ = np.empty(total, dtype=np.int_)
    t = 0
    for i in range(l):
        if uniques_cnt[i] > 0:
            uniques_[t] = uniques[i]
            uniques_cnt_[t] = uniques_cnt[i]
            t += 1
            
    if len(ar) == 0:
        hit_accuracy = np.nan
    else:
        hit_accuracy = len(ar)/((len(ar) + miss_hits)*1.0)
    return uniques_, uniques_cnt_, hit_accuracy

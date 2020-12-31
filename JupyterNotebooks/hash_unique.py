
# don't remove the follows for your use
# Author: https://lhprojects.github.io/blog/
# don't remove above lines

import numba
import numpy as np


def unique(ar, weights = None, return_counts = False, return_hit_accuracy = False):
    '''
    ar: integer array
    return:
        uniques [, uniques_counts] [, hit_accuracy]
        hit_accuracy should be close to 1. unless
        the hash function has some quality problem
    '''
    if weights is not None:
        f,s,t = unique_impl64_w(ar, weights)
    else:
        f,s,t = unique_impl64(ar)
        
    if return_counts and return_hit_accuracy:
        return f, s, t
    elif return_counts:
        return f, s
    elif return_hit_accuracy:
        return f, t
    else:
        return f
    
def unique32(ar, weights = None, return_counts = False, return_hit_accuracy = False):
    '''
    ar: integer array
    NOTE: upper 32 bits ignored for hash function
    return:
        uniques [, uniques_counts] [, hit_accuracy]
        hit_accuracy should be close to 1. unless
        the hash function has some quality problem
    '''
    
    if weights is not None:
        f,s,t = unique_impl32_w(ar, weights)
    else:
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
    l = int(np.ceil(np.log2(l)))
    # 4*len(ar) > l > 2*len(ar)
    l = 2 << l
    return l

@numba.njit
def FNV_1_64(v):
    # https://en.wikipedia.org/wiki/Fowler%E2%80%93Noll%E2%80%93Vo_hash_function
    
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
def make_hash_table(ar):
    l = length(len(ar))    
    mask = l - 1      
    
    uniques = np.empty(l, dtype=ar.dtype)
    uniques_cnt = np.zeros(l, dtype=np.int_)
    return uniques, uniques_cnt, l, mask

@numba.njit
def make_hash_table_w(ar):
    l = length(len(ar))    
    mask = l - 1      
    
    uniques = np.empty(l, dtype=ar.dtype)
    uniques_cnt = np.zeros(l, dtype=np.int_)
    uniques_weight = np.zeros(l, dtype=np.float_)
    return uniques, uniques_cnt, uniques_weight, l, mask

@numba.njit
def set_item(uniques, uniques_cnt, mask, h, v, total, miss_hits, weight):
        
    index = (h & mask)

    # open address hash
    # great cache performance
    while True:
        if uniques_cnt[index] == 0:
            # insert new
            uniques_cnt[index] += weight
            uniques[index] = v
            total += 1
            break
        elif uniques[index] == v:
            uniques_cnt[index] += weight
            break
        else:
            miss_hits += 1
            index += 1
            index = index & mask
    return total, miss_hits
    
@numba.njit
def set_item_w(uniques, uniques_cnt, uniques_weights, mask, h, v, w, total, miss_hits):
        
    index = (h & mask)

    # open address hash
    # great cache performance
    while True:
        if uniques_cnt[index] == 0:
            # insert new
            uniques_cnt[index] += 1
            uniques_weights[index] += w
            uniques[index] = v
            total += 1
            break
        elif uniques[index] == v:
            uniques_cnt[index] += 1
            uniques_weights[index] += w
            break
        else:
            miss_hits += 1
            index += 1
            index = index & mask
    return total, miss_hits
    
@numba.njit
def concrete(ar, uniques, uniques_cnt, l, total):
    # flush the results in a concrete array            
    uniques_ = np.empty(total, dtype=ar.dtype)
    uniques_cnt_ = np.empty(total, dtype=np.int_)
    t = 0
    for i in range(l):
        if uniques_cnt[i] > 0:
            uniques_[t] = uniques[i]
            uniques_cnt_[t] = uniques_cnt[i]
            t += 1
    return uniques_, uniques_cnt_

@numba.njit
def concrete_w(ar, uniques, uniques_cnt, uniques_weight, l, total):
    # flush the results in a concrete array            
    uniques_ = np.empty(total, dtype=ar.dtype)
    uniques_cnt_ = np.empty(total, dtype=np.int_)
    uniques_weight_ = np.empty(total, dtype=np.float_)
    t = 0
    for i in range(l):
        if uniques_cnt[i] > 0:
            uniques_[t] = uniques[i]
            uniques_cnt_[t] = uniques_cnt[i]
            uniques_weight_[t] = uniques_weight[i]
            t += 1
    return uniques_, uniques_cnt_, uniques_weight_

def unique_factor(hash_function):
    
    @numba.njit
    def unique_impl(ar):

        uniques, uniques_cnt, l, mask = make_hash_table(ar)
        total = 0    
        miss_hits = 0    

        for v in ar:
            h = hash_function(v)
            total, miss_hits = set_item(uniques, uniques_cnt, mask, h, v, total, miss_hits, 1)

        uniques_, uniques_cnt_ = concrete(ar, uniques, uniques_cnt, l, total)

        if len(ar) == 0:
            hit_accuracy = np.nan
        else:
            hit_accuracy = len(ar)/((len(ar) + miss_hits)*1.0)
        return uniques_, uniques_cnt_, hit_accuracy
    
    return unique_impl


def unique_factor_w(hash_function):
    
    @numba.njit
    def unique_impl_w(ar, weights):

        uniques, uniques_cnt, uniques_weight, l, mask = make_hash_table_w(ar)
        total = 0    
        miss_hits = 0    

        for i, v in enumerate(ar):
            h = hash_function(v)
            w = weights[i]
            total, miss_hits = set_item_w(uniques, uniques_cnt, uniques_weight, mask, h, v, w, total, miss_hits)
            
        uniques_, uniques_cnt_, uniques_weight_ = concrete_w(ar, uniques, uniques_cnt, uniques_weight, l, total)

        if len(ar) == 0:
            hit_accuracy = np.nan
        else:
            hit_accuracy = len(ar)/((len(ar) + miss_hits)*1.0)
        return uniques_, uniques_weight_, hit_accuracy
    
    return unique_impl_w

unique_impl64 = unique_factor(FNV_1_64)
unique_impl32 = unique_factor(FNV_1_32)
unique_impl64_w = unique_factor_w(FNV_1_64)
unique_impl32_w = unique_factor_w(FNV_1_32)

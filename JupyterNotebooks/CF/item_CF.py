
from .inverse_links import InverseLinks
import numpy as np
import numba
import hash_unique

@numba.njit
def collect_links(i, links, page_n_links, page_start,
                  links_inverse, page_n_links_inverse, page_start_inverse,
                  links_):
    
    total = 0    
    start1 = page_start_inverse[i]
    n_pages1 = page_n_links_inverse[i]
    
    # all pages that links to this
    for l1 in range(start1, start1 + n_pages1):
        l1_ = links_inverse[l1]
        
        
        start2 = page_start[l1_]
        n_pages2 = page_n_links[l1_]
        
        # all pages that page(l1_) links to
        for l2 in range(start2, start2+n_pages2):
            l2_ = links[l2]
            links_[total] = l2_
            total += 1
            
    return total
    
def itemitem(i, links, page_n_links, page_start,
             links_inverse, page_n_links_inverse, page_start_inverse,
             weights_inter = None, weights_final = None, 
             links_ = None):
    
    if links_ is None:
        links_  = np.empty(len(links), np.int)
    
    total = collect_links(i, links, page_n_links, page_start,
                  links_inverse, page_n_links_inverse, page_start_inverse, links_)
    
    links_ = links_[:total]
    
    # this is the slowest step
    # uns, uns_w = np.unique(links_, return_counts=True)
    if weights_inter is not None:
        link_weights = weights_inter[links_]
        uns, uns_w = hash_unique.unique32(links_, weights = link_weights, return_counts=True)
    else:
        uns, uns_w = hash_unique.unique32(links_, return_counts=True)
        uns_w = np.array(uns_w, dtype=np.float)

    if weights_final is not None:
        uns_w *= weights_final[uns]

    uns_w = uns_w/(np.sqrt(page_n_links_inverse[uns])*np.sqrt(page_n_links_inverse[i]))
    
    if len(uns) > 11:
        indices = np.argpartition(uns_w, -11)[-11:]
        uns = uns[indices]
        uns_w = uns_w[indices]
        
    # inverse and skip the largest
    indices = np.argsort(uns_w)[::-1][1:]
    return uns[indices], uns_w[indices]
            

        
    

class ItemCF:
        
    def __init__(self,  links, inverse_links = None, weights = None, titles = None):
        self.links = links
        self.titles = titles        
        if inverse_links is None:
            inverse_links = InverseLinks(links = links, titles = titles)            
        self.inverse_links = inverse_links
        self.weights = weights

    def pages_link_to_this_page_also_link_to(self, i, use_weights_inter = False, use_weights_final = False):
        links = self.links.links
        page_n_links = self.links.page_n_links
        page_start = self.links.page_start
        
        links_inverse = self.inverse_links.links_inverse
        page_n_links_inverse = self.inverse_links.page_n_links_inverse
        page_start_inverse = self.inverse_links.page_start_inverse

        weights_inter = None
        if use_weights_inter:
            weights_inter = self.weights

        weights_final = None
        if use_weights_final:
            weights_final = self.weights
        

        uns = itemitem(i, links, page_n_links, page_start,
                      links_inverse, page_n_links_inverse, page_start_inverse,
                      weights_inter = weights_inter, weights_final = weights_final)
        return uns

    def pages_this_page_link_to_also_linked_by(self, i, use_weights_inter = False, use_weights_final = False):
        links = self.links.links
        page_n_links = self.links.page_n_links
        page_start = self.links.page_start
        
        links_inverse = self.inverse_links.links_inverse
        page_n_links_inverse = self.inverse_links.page_n_links_inverse
        page_start_inverse = self.inverse_links.page_start_inverse
        
        weights_inter = None
        if use_weights_inter:
            weights_inter = self.weights

        weights_final = None
        if use_weights_final:
            weights_final = self.weights

        uns = itemitem(i, links_inverse, page_n_links_inverse, page_start_inverse,
                      links, page_n_links, page_start,
                      weights_inter = weights_inter, weights_final = weights_final)    
        return uns

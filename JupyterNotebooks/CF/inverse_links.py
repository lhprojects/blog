import numpy as np
import numba
    
class InverseLinks:
    
    def __init__(self, links, titles = None):                        
        self.titles = titles
        self.links = links
                
        page_n_links = links.page_n_links
        page_start = links.page_start
        links = links.links

        n_pages = len(page_n_links)
        inverse_link = [[] for i in range(n_pages)]

        for lk in range(n_pages):        
            n_links = page_n_links[lk]
            start = page_start[lk]

            for j in range(start, start+n_links): 
                this = links[j]            
                inverse_link[this].append(lk)

        links_inverse = np.empty(shape=len(links), dtype=np.int)
        page_n_links_inverse = np.empty(shape=len(page_n_links), dtype=np.int)

        l = 0
        for i, lks in enumerate(inverse_link):
            page_n_links_inverse[i] = len(lks)
            if len(lks):
                links_inverse[l:l+len(lks)] = lks
                l += len(lks)

        page_start_inverse = np.zeros(len(page_n_links_inverse), dtype=np.int)
        page_start_inverse[1:] = np.cumsum(page_n_links_inverse)[:-1]

        assert page_n_links_inverse.sum() == len(links_inverse)

        self.links_inverse = links_inverse
        self.page_n_links_inverse = page_n_links_inverse
        self.page_start_inverse = page_start_inverse

    def get_links_from_title_inverse(self, title):
        titles = self.titles
        
        index = titles.get_index_from_title(title)
        if index is not None:
            s = self.page_start_inverse[index]
            n = self.page_n_links_inverse[index]
            return [titles.get_title_from_index(i) for i in self.links_inverse[s:s+n] ]
    

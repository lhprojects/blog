import pickle
import numpy as np
from .wiki_titles import WikiTitles
    
class WikiLinks:

    def __init__(self, file, wiki_titles = None):
        
        self.wiki_titles = wiki_titles
            
        with np.load(file) as data:
            links = data['links']
            page_n_links = data['page_n_links']

        page_start = np.zeros(len(page_n_links), dtype=np.int)
        page_start[1:] = np.cumsum(page_n_links)[:-1]
        assert(page_n_links.sum() == len(links))

        self.links = links
        self.page_n_links = page_n_links        
        self.page_start = page_start        
    
    def get_links_from_title(self, title):
        wiki_titles = self.wiki_titles
        index = wiki_titles.get_index_from_title(title)
        if index is not None and index >= 0:
            s = self.page_start[index]
            n = self.page_n_links[index]
            return [wiki_titles.get_title_from_index(i) for i in self.links[s:s+n] ]

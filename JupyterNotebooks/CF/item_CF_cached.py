
import numpy as np

class ItemCFCached:
    
    def __init__(self, pages_link_to_this_page_also_link_to, 
                 pages_this_page_link_to_also_linked_by,
                 titles = None):
            
        self.titles = titles
        
        with np.load(pages_link_to_this_page_also_link_to) as data:
            self.pages_link_to_this_page_also_link_to_ = data['arr_0']

        with np.load(pages_this_page_link_to_also_linked_by) as data:
            self.pages_this_page_link_to_also_linked_by_ = data['arr_0']
            
    def pages_link_to_this_page_also_link_to(self, i):
        if i is not None and i >= 0 and i < len(self.pages_link_to_this_page_also_link_to_):
            uns = self.pages_link_to_this_page_also_link_to_[i]
            return uns
    

    def pages_this_page_link_to_also_linked_by(self, i):
        if i is not None and i >= 0 and i < len(self.pages_this_page_link_to_also_linked_by_):
            uns = self.pages_this_page_link_to_also_linked_by_[i]
            return uns
        
    def pages_link_to_this_page_also_link_to_title(self, this_page):
        i = self.titles.get_index_from_title(this_page)
        if i is not None and i >= 0 and i < len(self.pages_link_to_this_page_also_link_to_):
            uns = self.pages_link_to_this_page_also_link_to(i)
            titles = [self.titles.get_title_from_index(pid) for pid in uns]
            return titles
        
    def pages_this_page_link_to_also_linked_by_title(self, this_page):
        i = self.titles.get_index_from_title(this_page)
        if i is not None and i >= 0 and i < len(self.pages_this_page_link_to_also_linked_by_):
            uns = self.pages_this_page_link_to_also_linked_by(i)
            titles = [self.titles.get_title_from_index(pid) for pid in uns]
            return titles

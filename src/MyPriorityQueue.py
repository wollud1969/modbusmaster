import queue


class MyPriorityQueueItem(object):
    def __init__(self, itemWithPriority):
        self.itemWithPriority = itemWithPriority

    def __lt__(self, other): return self.itemWithPriority.priority < other.itemWithPriority.priority

    def __le__(self, other): return self.itemWithPriority.priority <= other.itemWithPriority.priority

    def __eq__(self, other): return self.itemWithPriority.priority == other.itemWithPriority.priority

    def __ne__(self, other): return self.itemWithPriority.priority != other.itemWithPriority.priority

    def __gt__(self, other): return self.itemWithPriority.priority > other.itemWithPriority.priority
    
    def __ge__(self, other): return self.itemWithPriority.priority >= other.itemWithPriority.priority


class MyPriorityQueue(queue.PriorityQueue):
    def _put(self, itemWithPriority):
        i = MyPriorityQueueItem(itemWithPriority)
        super()._put(i)

    def _get(self):
        i = super()._get()
        return i.itemWithPriority

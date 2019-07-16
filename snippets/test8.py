import unittest
import json

class A(object):
    def __init__(self, arg1=None, arg2=None):
        self.arg1 = arg1
        self.arg2 = arg2
        self.arg3 = self.arg1 + self.arg2

    def __str__(self):
        return "A: {0!s} {1!s} {2!s}".format(self.arg1, self.arg2, self.arg3)

    def jsonify(self):
        return {'type':self.__class__.__name__, 'args': {'arg1':self.arg1, 'arg2':self.arg2}}

class MyEncoder(json.JSONEncoder):
    def default(self, o):
        try:
            return o.jsonify()
        except TypeError or AttributeError:
            return super().default(o)


def objectFactory(j):
    klass = eval(j['type'])
    o = klass(**j['args'])
    return o

def MyDecoder(j):
    if type(j) == dict and 'type' in j:
        return objectFactory(j)
    else:
        return j

class Tests(unittest.TestCase):
    def test_a1(self):
        a1 = A(1, 2)
        self.assertEqual(a1.arg1, 1)
        self.assertEqual(a1.arg2, 2)
        self.assertEqual(a1.arg3, 3)

    def test_a2(self):
        a2 = A(**{'arg1':2, 'arg2':4})
        self.assertEqual(a2.arg1, 2)
        self.assertEqual(a2.arg2, 4)
        self.assertEqual(a2.arg3, 6)

    def test_a3(self):
        j = '{ "type": "A", "args": { "arg1": 3, "arg2": 5 } }'
        jj = json.loads(j)
        klass = eval(jj['type'])
        self.assertEqual(A, klass)
        a3 = klass(**jj['args'])
        self.assertEqual(a3.arg1, 3)
        self.assertEqual(a3.arg2, 5)
        self.assertEqual(a3.arg3, 8)

    def test_a4(self):
        j = '{ "type": "A", "args": { "arg1": 3, "arg2": 5 } }'
        jj = json.loads(j)
        klass = eval(jj['type'])
        self.assertEqual(A, klass)
        a3 = klass(**jj['args'])
        self.assertEqual(a3.arg1, 3)
        self.assertEqual(a3.arg2, 5)
        self.assertEqual(a3.arg3, 8)

        jjjj = json.dumps(a3, cls=MyEncoder)

        jjj = json.loads(jjjj)
        klass = eval(jjj['type'])
        self.assertEqual(A, klass)
        a3 = klass(**jjj['args'])
        self.assertEqual(a3.arg1, 3)
        self.assertEqual(a3.arg2, 5)
        self.assertEqual(a3.arg3, 8)

    def test_a5(self):
        jList = []
        jList.append(objectFactory({'type':'A', 'args': {'arg1':1, 'arg2':2}}))
        jList.append(objectFactory({'type':'A', 'args': {'arg1':2, 'arg2':3}}))
        jList.append(objectFactory({'type':'A', 'args': {'arg1':3, 'arg2':4}}))

        js = json.dumps(jList, cls=MyEncoder, sort_keys=True, indent=4)

        print(js)

        jResultList = json.loads(js, object_hook=MyDecoder)

        self.assertEqual(jResultList[0].arg1, 1)
        self.assertEqual(jResultList[0].arg2, 2)
        self.assertEqual(jResultList[0].arg3, 3)

        self.assertEqual(jResultList[1].arg1, 2)
        self.assertEqual(jResultList[1].arg2, 3)
        self.assertEqual(jResultList[1].arg3, 5)

        self.assertEqual(jResultList[2].arg1, 3)
        self.assertEqual(jResultList[2].arg2, 4)
        self.assertEqual(jResultList[2].arg3, 7)



if __name__ == '__main__':
    unittest.main()

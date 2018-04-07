"""
Christina Hernandez Wunsch <hernandezwunschc@gmail.com>
"""

import re
import sys
import operator


class QgramIndex:
    """ A simple Q-Gram index """

    def __init__(self, q):
        """ Create an empty inverted index. """

        self.inverted_lists = {}
        self.q = q
        self.records = []
        self.original_records = []
        self.city_names = []

    def read_from_file(self, file_name):
        """
        Construct from given file (one record per line).

        file_name: [string] The file you want to process
        """
        with open(file_name) as file:
            record_id = 0
            for line in file:
                name = str(line).split("\t")
                record_id += 1
                self.city_names.append(name[0])
                self.original_records.append(line)
                # replacing the leftmost non-overlapping occurrences
                line = re.sub("\W+", "", line).lower()
                self.records.append(line)
                for qgram in self.get_qgrams(line):
                    if len(qgram) > 0:
                        # check if the qgram's already there
                        if qgram not in self.inverted_lists:
                            self.inverted_lists[qgram] = list()
                        self.inverted_lists[qgram].append(record_id)

    def get_qgrams(self, record):
        '''
        All qgrams for given record.
        '''
        qgrams = []
        padding = "$" * (self.q - 1)
        record = padding + record
        for i in range(0, len(record) - self.q + 1):
            qgrams.append(record[i:i + self.q])
        return qgrams

    def merge(self, inv_lists):
        """
        merges the inverted lists for a given set of q-grams.
        """
        counter_dictionary = {}
        for i in range(len(inv_lists)):
            for j in range(len(inv_lists[i])):
                element = inv_lists[i][j]
                if element not in counter_dictionary:
                    counter_dictionary[element] = 1
                else:
                    counter_dictionary[element] += 1

        return counter_dictionary

    def ped(self, p, s, delta):
        """
        Compute the prefix edit distance
        """
        rows = len(p) + 1
        cols = len(s) + 1
        if (delta > -1):
            cols = min(cols, len(p) + delta + 1)
        vals = [[0 for x in range(cols)] for x in range(rows)]
        # initialize first row and first column
        for i in range(rows):
            vals[i][0] = i
        for i in range(cols):
            vals[0][i] = i
        # compute values
        for i in range(1, rows):
            for j in range(1, cols):
                candidates = [0, 0, 0]
                # insert
                candidates[0] = vals[i][j - 1] + 1
                # delete
                candidates[1] = vals[i - 1][j] + 1
                # replace (if unequal) or nothing (if equal)
                if (p[i - 1] != s[j - 1]):
                    candidates[2] = vals[i - 1][j - 1] + 1
                else:
                    candidates[2] = vals[i - 1][j - 1]
                vals[i][j] = min(candidates)
        # ped is the smallest value in the last row
        return min(vals[rows - 1])

    def find_matches(self, prefix, delta, k):
        """
        Finds all entities y with PED(x, y) ≤ δ
        k = number of cities we want to be displayed
        """
        # padding prefix and compute qgrams
        qgrams = self.get_qgrams(prefix)
        # combine lists
        lists = []
        for qgram in qgrams:
            if qgram in self.inverted_lists:
                lists.append(self.inverted_lists[qgram])
        # merge lists
        list_dict = self.merge(lists)
        # compute output
        output = {}
        peds = 0
        for key in list_dict:
            len_x = len(prefix)
            if (list_dict[key] >= len_x - self.q * delta):
                # compute ped
                ped = self.ped(prefix, self.records[key - 1], delta)
                peds += 1
                if ped <= delta:
                    output[key] = float(ped) / max(delta, 1) \
                        + float(key) / len(self.records)
        return sorted(
            output.items(),
            key=operator.itemgetter(1)
        )[0:min(len(output), k)], peds


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 qgram_index.py <file>")
        sys.exit()
    file_name = sys.argv[1]
    qi = QgramIndex(3)
    print("reading...")
    qi.read_from_file(file_name)
    while True:
        sys.stdout.write("query : ")
        query = input()
        if query == "exit":
            sys.exit(0)
        query = re.sub("\W+", "", query).lower()
        answers, ped = qi.find_matches(query, len(query) // 4, 5)
        print("[computed %i peds]" % ped)
        for a in answers:
            print("%s (rating = %f)" % (qi.original_records[a[0] - 1], a[1]))

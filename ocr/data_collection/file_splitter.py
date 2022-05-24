#!/usr/bin/env python
import os
import sys


class FileSplitter:
    def __init__(self):
        self.parse_args(sys.argv)

    @staticmethod
    def run():
        splitter = FileSplitter()
        splitter.split()

    def split(self):
        file_number = 1
        line_number = 1

        print("Splitting", os.path.join(self.working_dir, self.file_base_name + self.file_ext),
              "into multiple files with", self.split_size, "lines")

        out_file = self.get_new_file(file_number)
        for line in self.in_file:
            out_file.write(line)
            line_number += 1
            if line_number == self.split_size + 1:
                out_file.close()
                file_number += 1
                line_number = 1
                out_file = self.get_new_file(file_number)

        out_file.close()

        print("Created %s files." % (str(file_number)))

    def get_new_file(self, file_number):
        """return a new file object ready to write to"""
        new_file_name = "%s%s%s" % (self.file_base_name, str(file_number), self.file_ext)
        new_file_path = os.path.join(self.working_dir, new_file_name)
        print("creating file %s" % (new_file_path))
        return open(new_file_path, 'w')

    def parse_args(self, argv):
        """parse args and set up instance variables"""
        try:
            self.split_size = 1000
            if len(argv) > 2:
                self.split_size = int(argv[2])
            self.file_name = argv[1]
            self.in_file = open(self.file_name, "r")
            self.working_dir = os.getcwd()
            self.file_base_name, self.file_ext = os.path.splitext(self.file_name)
        except:
            print(self.usage())
            sys.exit(1)

    def usage(self):
        return """
        Split a large file into many smaller files with set number of rows.
        Usage:
            $ python file_splitter.py <file_name> [row_count]
        row_count is optional (default is 1000)
        """


if __name__ == "__main__":
    FileSplitter.run()

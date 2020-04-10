import argparse
import random
import typing
from io import TextIOWrapper

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('--input-src', required=True, help='Path to source language input file')
  parser.add_argument('--input-tgt', required=True, help='Path to target language input file')
  parser.add_argument('--output-src', required=True, help='Path to source language output file')
  parser.add_argument('--output-tgt', required=True, help='Path to target language output file')
  parser.add_argument('--validate-alignment', action='store_true', help='Validate alignment of parallel corpora after processing')
  args = parser.parse_args()
  deduplicate(args.input_src, args.input_tgt, args.output_src, args.output_tgt)
  if (args.validate_alignment):
    validate_alignment(args.input_src, args.input_tgt, args.output_src, args.output_tgt)

def deduplicate(input_src: str, input_tgt: str, output_src: str, output_tgt: str) -> None:
  """
  Deduplicates a parallel corpus.
  """
  input_src_file = open(input_src, 'r')
  input_tgt_file = open(input_tgt, 'r')
  output_src_file = open(output_src, 'w')
  output_tgt_file = open(output_tgt, 'w')  
  deduplicate_streams(input_src_file, input_tgt=input_tgt_file, output_src=output_src_file, output_tgt=output_tgt_file)
      
def deduplicate_streams(input_src: TextIOWrapper, input_tgt: TextIOWrapper, output_src: TextIOWrapper, output_tgt: TextIOWrapper) -> None:
  """
  Deduplicates a parallel corpus.
  """
  # Hashes of strings we've encountered during deduplication
  matched_strings = set()
  
  # Step through both corpora
  # If neither line matches one we've seen before,
  # write it to the depduplicated corpora
  for line_src, line_tgt in zip(input_src, input_tgt):
    line_src = line_src.rstrip('\n')
    line_tgt = line_tgt.rstrip('\n')
    hash_src = hash(line_src)
    hash_tgt = hash(line_tgt)
    matched_src = hash_src in matched_strings
    matched_tgt = hash_tgt in matched_strings
    if not matched_src:
      matched_strings.add(hash_src)
    if not matched_tgt:
      matched_strings.add(hash_tgt)
    if not matched_src and not matched_tgt:
      print(line_src, file=output_src)
      print(line_tgt, file=output_tgt)

def count_lines(stream: TextIOWrapper) -> int:
  return sum(1 for line in stream)
  
def validate_alignment(input_src: str, input_tgt: str, output_src: str, output_tgt: str) -> None:
  """
  Spot-checks original and deduplicated corpora to verify that text alignment was preserved during deduplication.
  """
  input_src_file_length = count_lines(open(input_src, 'r'))
  input_tgt_file_length = count_lines(open(input_tgt, 'r'))
  output_src_file_length = count_lines(open(output_src, 'r'))
  output_tgt_file_length = count_lines(open(output_tgt, 'r'))
  assert(input_src_file_length == input_tgt_file_length)
  assert(output_src_file_length == output_tgt_file_length)  
  input_src_file = open(input_src, 'r')
  input_tgt_file = open(input_tgt, 'r')
  output_src_file = open(output_src, 'r')
  output_tgt_file = open(output_tgt, 'r')
  input_line_now = -1
  output_line_now = 0
  output_line_next = 0
  for output_line_src, output_line_tgt in zip(output_src_file, output_tgt_file):
    while True:
      input_line_src = input_src_file.readline()
      input_line_tgt = input_tgt_file.readline()
      input_line_now += 1
      if len(input_line_src) == 0 or len(input_line_tgt) == 0:
        raise Exception(f"Didn't find line in input corpus matching:\nSource:\n{output_line_src}\nTarget:\n{output_line_tgt}")
      matched_src = input_line_src == output_line_src
      matched_tgt = input_line_tgt == output_line_tgt
      if matched_src and matched_tgt:
        print(f"Found correct alignment for output line {output_line_now} on input line {input_line_now}: ({input_line_src[0:16].rstrip()}..., {input_line_tgt[0:16].rstrip()}...)")
        break
      if matched_src or matched_tgt:
        raise Exception(f"Found misalignment.\nInput source:\n{input_line_src}\nInput target:\n{input_line_tgt}\nOutput source:\n{output_line_src}\nOutput target:\n{output_line_tgt}")        
    output_line_now += 1

if __name__ == '__main__':
  main()

// This is the code that was used to produce the various .txt sequences
// that we compare against in the tests.

// Compile with something like:
// g++ compat.cpp -Wall -Wextra -I ~/Desktop/pcg-cpp-0.98/include -std=c++11
#include <iostream>
#include <iomanip>
#include <string>
#include <map>
#include <random>
#include <cmath>
#include "pcg_random.hpp"

using namespace std;

int main()
{
  pcg_engines::setseq_xsh_rr_64_32 rng1(42u, 54u);
  for (int i = 0; i < 32; ++i) {
    cout << "0x" << hex << setfill('0') << setw(8) << rng1() << endl;
  }
  cout << endl;

  pcg_engines::oneseq_xsh_rr_64_32 rng2(123u);
  for (int i = 0; i < 32; ++i) {
    cout << "0x" << hex << setfill('0') << setw(8) << rng2() << endl;
  }
  cout << endl;

  pcg_engines::setseq_xsh_rs_64_32 rng3(42u, 54u);
  for (int i = 0; i < 32; ++i) {
    cout << "0x" << hex << setfill('0') << setw(8) << rng3() << endl;
  }
  cout << endl;

  pcg_engines::oneseq_xsh_rs_64_32 rng4(123u);
  for (int i = 0; i < 32; ++i) {
    cout << "0x" << hex << setfill('0') << setw(8) << rng4() << endl;
  }
  cout << endl;

  pcg_engines::setseq_xsl_rr_128_64 rng5(42u, 54u);
  for (int i = 0; i < 32; ++i) {
    cout << "0x" << hex << setfill('0') << setw(16) << rng5() << endl;
  }
  cout << endl;

  pcg_engines::oneseq_xsl_rr_128_64 rng6(123u);
  for (int i = 0; i < 32; ++i) {
    cout << "0x" << hex << setfill('0') << setw(16) << rng6() << endl;
  }
  cout << endl;

  return 0;
}

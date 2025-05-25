# We're trying to speed things up

Goal: under 50ms.
We will save to tar -> probably will switch architecture of datamule towards tar?
hmm does tar let us do database ops?
yep. this might be slightly slower metadata load times, but much faster overall for e.g. forms 345 etc.
would play into tar rewrite better and http ranges thingy.



SECSGML (cython)
90 milliseconds

New Test: (python)
* parsing - 10 milliseconds
* writing - 15ms

Writing:
many async - 40ms
one big file - 18ms
one big tar - 26ms

so lets try adding cython to the mix

parsing : 7.6ms 

Cython
parsing doesnt seem faster

# ok so
probably just rewrite in python, maybe get 2x perf boost - 45ms, and more robust and debuggable

so. we can probably just modify find to get the thing before <TEXT>
so file splitting is probably same speed,
we collect document metadata, submission metadata, do normal boring stuff, but protected....
modular so easy to debug, python so easy to debug
uu encoding becomes real bottleneck - that may or may not need a cython rewrite.
-> so 30ms without uuencoding tackling
if uu encoding adds less than 50pct overhead its worth it.
45ms-> 20 10-Ks in one second, single threaded. yeah that seems fine.


# Ideas
so...maybe we just do a seeker? - seeking is ridiculously fast
right we need metadata with byte range....
seeking is really fast... like basically 1/1000 of time.
probably worth implementing anyway...

but then how do we square the compression?
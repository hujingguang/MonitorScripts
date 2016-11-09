#!/usr/bin/python


def insert_sort():
    array=[]
    s=raw_input('please input numbers for insert sort: ')
    for i in s.split(' '):
	try:
	    array.append(int(i))
	except:
	    pass
    n=len(array)
    for i in range(1,n):
	now,point=i-1,i
	while now>=0:
	    if array[point]<array[now]:
		now=now-1
	    else:
		break
	now=now+1
	for j in range(point,now,-1):
	    array[j],array[j-1]=array[j-1],array[j]
	print array


if __name__=='__main__':
    insert_sort()


	






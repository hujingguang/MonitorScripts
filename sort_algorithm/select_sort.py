#!/usr/bin/python


def select_sort():
    array=[]
    s=raw_input('please input numbers for select sort: ')
    for n in s.split(' '):
	try:
	    array.append(int(n))
	except:
	    pass
    n=len(array)
    for j in range(0,n-1):
	min,i=j,j+1
	while i <n:
	    if array[min]>array[i]:
		min=i
	    i=i+1
	if min != i:
	    array[min],array[j]=array[j],array[min]
	flag=True
	for i in range(1,n):
	    if array[i-1]>array[i]:
		flag=False
        if flag:
	    break
	print array
    print array
	    



if __name__=='__main__':
    select_sort()






	

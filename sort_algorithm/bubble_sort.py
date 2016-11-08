#!/usr/bin/python


def bubble_sort():
   array=[]
   s=raw_input('please input numbers for bubble sort: ')
   for i in s.split(' '):
       try:
	   array.append(int(i))
       except:
	   pass
   n=len(array) 
   if len(array)<=1:
       print array
   for _ in range(1,n-1):
       j=0
       while j<n-1:
	   if array[j]>array[j+1]:
	       array[j],array[j+1]=array[j+1],array[j]
           j=j+1
       print array
   print array

if __name__=='__main__':
    bubble_sort()
   


*italics*
some_name_
`_somevariable_`

----

```python
def fizzbuzz(n):
    for i in range(1, n + 1):
        if i % 3 == 0 and i % 5 == 0:
            print("FizzBuzz")
        elif i % 3 == 0:
            print("Fizz")
        elif i % 5 == 0:
            print("Buzz")
        else:
            print(i)


# Example usage: Print FizzBuzz up to 100
fizzbuzz(100)

#  Example usage: different range:
fizzbuzz(20)

#Example usage:  one line output (list comprehension)
def fizzbuzz_oneline(n):
    print(["FizzBuzz" if i%3==0 and i%5==0 else "Fizz" if i%3==0 else "Buzz" if i%5==0 else i for i in range(1,n+1)])

fizzbuzz_oneline(30)
```


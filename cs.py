from timer import Timer
def quick_pow(m:int,n:int):
    res = 1
    while n:
        if n & 1:
            res *= m
        m *= m
        n >>= 1
    return res
Timer.time_execution("朴素算法",lambda :(lambda res:[res:=res *3 for _ in range(50000)] and res)(1))
Timer.time_execution("快速幂", lambda :quick_pow(3,50000))
Timer.time_execution("内置函数",lambda :pow(3,50000))


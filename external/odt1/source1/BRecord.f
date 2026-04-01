       subroutine BRecord(ifile,N,s)
       implicit none
       integer ifile, N, j, m, num, nabs
       double precision s(*), h(10000)
 100   format(E15.7)
 200   format(I6)
       if(N.lt.0) write(ifile,200) N
       nabs=abs(N)
       do j=1, nabs
        h(j)=s(j)
        if(abs(h(j)) .lt. 0.1d0**30) h(j)=0.d0	!prevents format problem
       enddo
       write(ifile,100) (h(m),m=1,nabs)
       call flush(ifile)
       return
       end

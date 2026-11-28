/* Heuristic fixed-cardinality set cover; no lower-bound claim. */
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#define W 7
#define BITS (W*64)
#define MAXK 64
typedef struct {uint64_t x[W];} Mask;
static Mask *boxes,target;
static uint32_t n,k;
static int *bycell[BITS],nc[BITS];
static uint64_t rng=0x638aa6cecbaf194dULL;
static unsigned rnd(unsigned n){rng^=rng<<13;rng^=rng>>7;rng^=rng<<17;return rng%n;}
static unsigned pop(Mask a){unsigned n=0;for(int i=0;i<W;i++)n+=__builtin_popcountll(a.x[i]);return n;}
static int bit(Mask a,int i){return a.x[i/64]>>(i%64)&1;}
static unsigned gain(Mask a,Mask b){unsigned n=0;for(int i=0;i<W;i++)n+=__builtin_popcountll(a.x[i]&b.x[i]);return n;}
static Mask missing(int *sol,int skip){Mask a=target;for(unsigned j=0;j<k;j++)if((int)j!=skip&&sol[j]>=0)for(int q=0;q<W;q++)a.x[q]&=~boxes[sol[j]].x[q];return a;}
static int random_bit(Mask a){unsigned p=pop(a);if(!p)return -1;unsigned r=rnd(p);for(int i=0;i<W;i++){uint64_t w=a.x[i];while(w){int b=__builtin_ctzll(w);if(!r--)return i*64+b;w&=w-1;}}return -1;}
int main(int argc,char **argv){
 if(argc<3||argc>4)return 2;
 long steps=strtol(argv[2],0,10);if(steps<=0)return 2;
 if(argc==4){rng=strtoull(argv[3],0,10);if(!rng)return 2;}
 FILE *f=fopen(argv[1],"rb");if(!f)return 2;
 if(fread(&n,4,1,f)!=1||fread(&k,4,1,f)!=1||!n||n>100000||!k||k>MAXK||fread(&target,sizeof target,1,f)!=1)return 2;
 boxes=malloc(n*sizeof *boxes);if(!boxes||fread(boxes,sizeof *boxes,n,f)!=n)return 2;fclose(f);
 for(int i=0;i<BITS;i++)if(bit(target,i)){bycell[i]=malloc(n*sizeof(int));if(!bycell[i])return 2;for(unsigned j=0;j<n;j++)if(bit(boxes[j],i))bycell[i][nc[i]++]=j;if(!nc[i])return 2;}
 int sol[MAXK],best[MAXK],bestgap=BITS; Mask hard={{0}}; unsigned elites=0;
 for(long t=0;t<steps;t++){
  if(t%1000==0){
   memset(&hard,0,sizeof hard);
   if(t&&rnd(3)){memcpy(sol,best,k*sizeof(int));for(unsigned j=0;j<k;j++)if(rnd(5)==0)sol[j]=-1;}
   else for(unsigned j=0;j<k;j++)sol[j]=-1;
   for(unsigned j=0;j<k;j++)if(sol[j]<0){
    Mask miss=missing(sol,-1);unsigned score=0;int sel=rnd(n);
    for(unsigned q=0;q<300;q++){int c=rnd(n);unsigned g=gain(boxes[c],miss);if(g>score){score=g;sel=c;}}
    sol[j]=sel;
   }
  }
  Mask miss=missing(sol,-1);unsigned gap=pop(miss);
  if((int)gap<bestgap){bestgap=gap;memcpy(best,sol,k*sizeof(int));fprintf(stderr,"step %ld gap %u",t,gap);for(unsigned j=0;j<k;j++)fprintf(stderr," %d",sol[j]);fputc(10,stderr);if(!gap){for(unsigned j=0;j<k;j++)printf("%d\n",sol[j]);return 0;}}
  if(gap<=4&&t%17==0&&elites<4000){
   fprintf(stderr,"elite %u",gap);for(unsigned j=0;j<k;j++)fprintf(stderr," %d",sol[j]);fputc(10,stderr);elites++;
  }
  if(t%71==0){for(int q=0;q<W;q++)hard.x[q]|=miss.x[q];}
  if(t%307==0)hard=miss;
  unsigned cost=gap+3*gain(miss,hard);
  int c=random_bit(miss);if(c<0)return 2;
  unsigned start=rnd(k),slot=start,bestslot=slot;int choice=-1;unsigned mingap=4*BITS+1;
  for(unsigned q=0;q<k;q++){
   slot=(start+q)%k;Mask rem=missing(sol,slot);unsigned old=pop(rem)+3*gain(rem,hard);Mask weighted=rem;for(int q=0;q<W;q++)weighted.x[q]&=hard.x[q];
   for(int r=0;r<32;r++){
    int j=bycell[c][rnd(nc[c])];unsigned g=old-gain(boxes[j],rem)-3*gain(boxes[j],weighted);
    if(g<mingap){mingap=g;choice=j;bestslot=slot;}
   }
   if(mingap==0)break;
  }
  if(choice>=0&&(mingap<=cost||rnd(100)<(t%1000<300?35:8)))sol[bestslot]=choice;
 }
 fprintf(stderr,"best uncovered %d\n",bestgap);return 3;
}

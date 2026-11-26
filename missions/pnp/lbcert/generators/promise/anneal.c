/* Bounded semantic circuit synthesis. No result is a proof until separately
 * audited and kernel checked. Search failure is never a lower bound. */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <inttypes.h>
typedef uint64_t U;
typedef struct {int op,a,b;} Gate;
typedef struct {Gate g[32];int score,out;} Ind;
static U input[32],target,full;
static int n,k,allow;
static U rng;
static uint32_t rnd(void){rng^=rng<<13;rng^=rng>>7;rng^=rng<<17;return (uint32_t)rng;}
static int pick(int a){return rnd()%(unsigned)a;}
static double unit(void){return rnd()/4294967296.0;}
static Gate rg(int i){int a=pick(n+i),b=pick(n+i);return (Gate){pick(allow?3:2)+1,a,b};}
static int fit(Ind *z){
 U v[64];memcpy(v,input,n*sizeof(U));int best=99,w=0;
 for(int i=0;i<n;i++){int e=__builtin_popcountll(v[i]^target);if(e<best){best=e;w=i;}}
 for(int i=0;i<k;i++){
  Gate q=z->g[i];U a=v[q.a],b=q.op==3?0:v[q.b];
  v[n+i]=q.op==1?a&b:q.op==2?a|b:full^a;
  int e=__builtin_popcountll(v[n+i]^target);if(e<=best){best=e;w=n+i;}
 }
 z->out=w;
 if(!best)return z->score=0;
 U live=UINT64_C(1)<<w;
 for(int i=k-1;i>=0;i--)if(live>>(n+i)&1){
  Gate q=z->g[i];live|=UINT64_C(1)<<q.a;if(q.op!=3)live|=UINT64_C(1)<<q.b;
 }
 return z->score=32*best+k-__builtin_popcountll(live>>n);
}
static void emit(Ind *z){
 printf("{\"solution\":[[");
 for(int i=0;i<k;i++){
  Gate q=z->g[i];printf("%s[\"%s\",[%d",i?",":"",q.op==1?"and":q.op==2?"or":"not",q.a);
  if(q.op!=3)printf(",%d",q.b);printf("]]");
 }
 printf("],%d]}\n",z->out);fflush(stdout);
}
static void mutate(Ind *z,int num){
 for(int q=0;q<num;q++){
  int i=pick(k),j=pick(6);Gate *g=&z->g[i];
  if(j==0)g->op=pick(allow?3:2)+1;
  else if(j==1||j==2)g->a=pick(n+i);
  else if(j==3||j==4)g->b=pick(n+i);
  else *g=rg(i);
 }
}
static double now(void){struct timespec s;clock_gettime(CLOCK_MONOTONIC,&s);return s.tv_sec+s.tv_nsec*1e-9;}
int main(int argc,char **argv){
 if(argc!=3)return 2;
 double seconds=atof(argv[1]);rng=strtoull(argv[2],0,10);if(!rng)rng=1;
 int rows;
 if(!(seconds>0&&seconds<=5)||scanf("%d%d%d%d%"SCNu64,&n,&rows,&k,&allow,&target)!=5||
    n<1||n>32||k<1||k>31||n+k>=64||rows<1||rows>64||(allow!=0&&allow!=1))return 2;
 full=rows==64?UINT64_MAX:(UINT64_C(1)<<rows)-1;
 if(target&~full)return 2;
 for(int i=0;i<n;i++)if(scanf("%"SCNu64,input+i)!=1||(input[i]&~full))return 2;
 Ind pool[128];
 for(int s=0;s<128;s++){
  for(int i=0;i<k;i++)pool[s].g[i]=rg(i);
  if(!fit(&pool[s])){emit(&pool[s]);return 0;}
 }
 double end=now()+seconds;
 while(now()<end){
  int a=pick(128),b=pick(128);Ind z=pool[pool[a].score<pool[b].score?a:b];
  int start=pick(128);double T=24.0+pick(32);
  for(int j=0;j<12000;j++){
   Ind v=z;
   if(pick(15)==0){Ind q=pool[pick(128)];int cut=pick(k);for(int i=cut;i<k;i++)v.g[i]=q.g[i];}
   else mutate(&v,1+(pick(6)==0)+(pick(25)==0));
   int s=fit(&v),d=s-z.score;
   if(!s){emit(&v);return 0;}
   if(d<=0||unit()<exp(-d/T))z=v;
   if(s<pool[start].score||pick(500)==0){pool[start]=v;start=pick(128);}
   T*=0.9997;if(T<1.0)T=1.0;
   if((j&255)==0&&now()>=end)return 3;
  }
  if(pick(4)==0){int x=pick(128);for(int i=0;i<k;i++)pool[x].g[i]=rg(i);if(!fit(&pool[x])){emit(&pool[x]);return 0;}}
 }
 return 3;
}

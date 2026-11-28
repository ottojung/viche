/* Bounded, heuristic witness search. The independent Python audit is mandatory. */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef struct {uint64_t mask; uint32_t id,trans;} Entry;
typedef struct {int a,b,o;} Gate;
#define CAP (1u<<22)
#define MAXG 20
static Entry *table;
static uint8_t best[65536];
static uint64_t roots[6];
static Gate g[MAXG];
static int m,seed;
static uint64_t mix(uint64_t x){x^=x>>30;x*=UINT64_C(0xbf58476d1ce4e5b9);x^=x>>27;x*=UINT64_C(0x94d049bb133111eb);return x^(x>>31);}
static Entry *lookup(uint64_t x){size_t i=mix(x)&(CAP-1);while(table[i].mask && table[i].mask!=x)i=(i+1)&(CAP-1);return table+i;}
static void check(void){
 uint64_t w[6+MAXG];memcpy(w,roots,sizeof roots);
 for(int j=0;j<m;j++)w[6+j]=g[j].o?(w[g[j].a]|w[g[j].b]):(w[g[j].a]&w[g[j].b]);
 uint64_t x=w[5+m];if(!x)return;
 Entry *e=lookup(x);
 if(e->mask!=x||best[e->id]<=m)return;
 best[e->id]=m;
 printf("%d %u %u %d",seed,e->id,e->trans,m);
 for(int j=0;j<m;j++)printf(" %d %d %d",g[j].a,g[j].b,g[j].o);
 puts("");fflush(stdout);
}
static int edits(int j,Gate *v){
 Gate old=g[j];int n=0;
 v[n++]=(Gate){old.a,old.b,old.o^1};
 for(int k=0;k<6+j;k++)if(k!=old.a&&k!=old.b){v[n++]=(Gate){k,old.b,old.o};v[n++]=(Gate){old.a,k,old.o};}
 return n;
}
int main(int argc,char **argv){
 if(argc!=3)return 2;
 table=calloc(CAP,sizeof *table);if(!table)return 2;
 memset(best,255,sizeof best);
 for(int i=0;i<6;i++)for(int r=0;r<64;r++)if((r>>i)&1)roots[i]|=UINT64_C(1)<<r;
 FILE *f=fopen(argv[1],"rb");if(!f)return 2;
 Entry e;size_t n=0;
 while(fread(&e,sizeof e,1,f)==1){if(!e.mask||e.id>=65536||e.trans>=1440||++n>CAP/2)return 2;*lookup(e.mask)=e;}
 if(ferror(f))return 2;
 fclose(f);
 f=fopen(argv[2],"r");if(!f)return 2;
 while(fscanf(f,"%d%d",&seed,&m)==2){
  if(m<1||m>MAXG)return 2;
  for(int i=0;i<m;i++)if(fscanf(f,"%d%d%d",&g[i].a,&g[i].b,&g[i].o)!=3||g[i].a<0||g[i].a>=6+i||g[i].b<0||g[i].b>=6+i||(g[i].o!=0&&g[i].o!=1))return 2;
  check();
  for(int i=0;i<m;i++){
   Gate orig=g[i],v[2*(6+MAXG)+1];int vn=edits(i,v);
   for(int a=0;a<vn;a++){
    g[i]=v[a];check();
    for(int j=i+1;j<m;j++){
     Gate old=g[j],u[2*(6+MAXG)+1];int un=edits(j,u);
     for(int b=0;b<un;b++){g[j]=u[b];check();}
     g[j]=old;
    }
   }
   g[i]=orig;
  }
 }
 fclose(f);free(table);return 0;
}

/* Full six-input truth-table live-set screen with cofactor cost pruning.
 * Untrusted research: hash collisions, supplied floor hints and the search
 * implementation are not a proof. Never promote a result as a receipt.
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#define MAX 20
#define N 6
typedef uint64_t W;
static W roots[N],goal,crit[N],fullcuts;
static W dom[12];static int floors[12],nf;
static uint64_t *tab,tm,fill;
static long long count,limit,pruned;
static int use_bmi2;
static inline W can(W x){return (x&1)?~x:x;}
static inline W mix(W h){h^=h>>33;h*=UINT64_C(0xff51afd7ed558ccd);h^=h>>33;h*=UINT64_C(0xc4ceb9fe1a85ec53);return h^(h>>33);}
static W pext_portable(W w,W m){W s=0,b=1;while(m){W t=m&-m;if(w&t)s|=b;m^=t;b<<=1;}return s;}
#if defined(__x86_64__) && defined(__GNUC__)
#include <immintrin.h>
__attribute__((target("bmi2"))) static W pext_fast(W w,W m){return _pext_u64(w,m);}
#endif
static W (*extract)(W,W)=pext_portable;
static inline W sep(W w){
 W r=0;unsigned off=0;
 for(int i=0;i<N;i++){W x=crit[i];if(!x)continue; r|=extract(w^(w>>(1<<i)),x)<<off;off+=__builtin_popcountll(x);}
 return r;
}
static inline W key(W *s,int n,int k,unsigned char *paid){
 W h=(k+1)*UINT64_C(0x9e3779b97f4a7c15)+n;
 for(int j=0;j<n;j++)h=mix(h^s[j]);
 W p=0;for(int i=0;i<nf;i++)p=(p<<4)|paid[i];
 return mix(h^p)|1;
}
static inline int known(W h){for(W i=h&tm;;i=(i+1)&tm){if(tab[i]==h)return 1;if(!tab[i])return 0;}}
static inline void add(W h){if(fill>tm*3/4)return;for(W i=h&tm;;i=(i+1)&tm){if(tab[i]==h)return;if(!tab[i]){tab[i]=h;fill++;return;}}}
static inline int insert(W *s,int n,W w){int i=n;while(i>0&&s[i-1]>w){s[i]=s[i-1];i--;}s[i]=w;return n+1;}
static int rec(W *s,int n,int k,unsigned char *paid){
 if(n==1&&s[0]==goal)return 1;
 if(!k||n-1>k)return 0;
 W h=key(s,n,k,paid);if(known(h))return 0;
 if(++count>limit){puts("limit");fprintf(stderr,"states=%lld pruned=%lld\n",count,pruned);exit(0);}
 for(int i=0;i<nf;i++){
  int constants=0;W d=dom[i];
  for(int j=0;j<n;j++){W a=s[j]&d;constants+=(a==0||a==d);}
  if(paid[i]+k-constants<floors[i]){pruned++;add(h);return 0;}
 }
 W se[MAX];for(int i=0;i<n;i++)se[i]=sep(s[i]);
 int extra=k+1-n;
 for(int i=0;i<n;i++)for(int j=i+1;j<n;j++){
  W a=s[i],b=s[j],rest[MAX],base=0;int nr=0;
  for(int t=0;t<n;t++)if(t!=i&&t!=j){rest[nr++]=s[t];base|=se[t];}
  W zs[4]={can(a&b),can(a|b),can(a&~b),can(b&~a)};
  for(int o=0;o<4;o++){
   W z=zs[o];if(!z)continue;
   int duplicate=0;for(int t=0;t<n;t++)if(s[t]==z){duplicate=1;break;}if(duplicate)continue;
   W c=base|sep(z);unsigned char next[12];
   int calc=0;
   for(int keep=0;keep<4;keep++){
    if((keep==3&&extra<2)||(keep&&extra<1))continue;
    if((c|((keep&1)?se[i]:0)|((keep&2)?se[j]:0))!=fullcuts)continue;
    if(!calc){
     for(int t=0;t<nf;t++){
      W d=dom[t],v=z&d;int free=(v==0||v==d);
      for(int l=0;l<n&&!free;l++){W u=s[l]&d;free=(u==v||u==(v^d));}
      next[t]=paid[t]+!free;
     }
     calc=1;
    }
    W child[MAX];memcpy(child,rest,nr*sizeof(W));int m=nr;
    if(keep&1)m=insert(child,m,a);
    if(keep&2)m=insert(child,m,b);
    m=insert(child,m,z);
    if(rec(child,m,k-1,next))return 1;
   }
  }
 }
 add(h);return 0;
}
int main(void){
 unsigned long long g;int k;
 if(scanf("%llx%d%lld%d",&g,&k,&limit,&nf)!=4||k<0||k>14||limit<1||nf<0||nf>12)return 2;
 goal=can(g);if(!goal)return 2;
 for(int i=0;i<N;i++)for(int r=0;r<64;r++)if(r>>i&1)roots[i]|=UINT64_C(1)<<r;
 unsigned np=0;
 for(int i=0;i<N;i++){crit[i]=(g^(g>>(1<<i)))&~roots[i];np+=__builtin_popcountll(crit[i]);}
 if(!np||np>64){puts("toolarge");return 0;}
 fullcuts=np==64?UINT64_MAX:(UINT64_C(1)<<np)-1;
 for(int i=0;i<nf;i++){
  int j,b,l;if(scanf("%d%d%d",&j,&b,&l)!=3||j<0||j>=N||b<0||b>1||l<0||l>14)return 2;
  dom[i]=b?roots[j]:~roots[j];floors[i]=l;
 }
#if defined(__x86_64__) && defined(__GNUC__)
 if(__builtin_cpu_supports("bmi2")){extract=pext_fast;use_bmi2=1;}
#endif
 uint64_t cap=1024;while(cap<(uint64_t)limit*2&&cap<(1ULL<<25))cap<<=1;
 tm=cap-1;tab=calloc(cap,sizeof(uint64_t));if(!tab){puts("limit");return 0;}
 unsigned char paid[12]={0};
 for(int mask=1;mask<(1<<N);mask++){
  W s[MAX];int m=0;W c=0;
  for(int i=0;i<N;i++)if(mask>>i&1){m=insert(s,m,roots[i]);c|=sep(roots[i]);}
  if(c!=fullcuts||m-1>k)continue;
  if(rec(s,m,k,paid)){puts("found");fprintf(stderr,"states=%lld pruned=%lld bmi2=%d\n",count,pruned,use_bmi2);return 0;}
 }
 puts("none");fprintf(stderr,"states=%lld pruned=%lld bmi2=%d\n",count,pruned,use_bmi2);return 0;
}

/* Small-width experimental live-set screen; untrusted, never a proof receipt.
 * Canonicalize complements, maintain sorted live words, prefilter cuts.
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
typedef __uint128_t W;
static W full,goal;
static uint64_t low;
static int p;
static uint64_t *tab,tm,fill;
static long long count,limit;
#define MAX 20
static inline W can(W w){return (w&1)?w^full:w;}
static inline uint64_t sep(W w){return (uint64_t)(w^(w>>p))&low;}
static inline uint64_t mix(uint64_t h){h^=h>>33;h*=0xff51afd7ed558ccdULL;h^=h>>33;h*=0xc4ceb9fe1a85ec53ULL;return h^(h>>33);}
static inline uint64_t key(W *s,int n,int k){
 uint64_t h=(k+1)*0x9e3779b97f4a7c15ULL+n;
 for(int j=0;j<n;j++)h=mix(h^(uint64_t)s[j])^(uint64_t)(s[j]>>64);
 return h|1;
}
static inline int known(uint64_t h){for(uint64_t i=h&tm;;i=(i+1)&tm){if(tab[i]==h)return 1;if(!tab[i])return 0;}}
static inline void add(uint64_t h){if(fill>tm*3/4)return;for(uint64_t i=h&tm;;i=(i+1)&tm){if(tab[i]==h)return;if(!tab[i]){tab[i]=h;fill++;return;}}}
static inline int insert(W *s,int n,W w){int i=n;while(i>0&&s[i-1]>w){s[i]=s[i-1];i--;}s[i]=w;return n+1;}
static int rec(W *s,int n,int k){
 if(n==1&&s[0]==goal)return 1;
 if(!k||n-1>k)return 0;
 uint64_t h=key(s,n,k);
 if(known(h))return 0;
 if(++count>limit){printf("limit\n");fprintf(stderr,"states=%lld\n",count);exit(0);}
 uint64_t se[MAX];for(int i=0;i<n;i++)se[i]=sep(s[i]);
 int extra=k+1-n;
 for(int i=0;i<n;i++)for(int j=i+1;j<n;j++){
  W a=s[i],b=s[j], rest[MAX];uint64_t base=0;int nr=0;
  for(int t=0;t<n;t++)if(t!=i&&t!=j){rest[nr++]=s[t];base|=se[t];}
  W zs[4]={can(a&b),can(a|b),can(a&(full^b)),can(b&(full^a))};
  for(int o=0;o<4;o++){
   W z=zs[o];if(!z)continue;
   int duplicate=0;for(int t=0;t<n;t++)if(s[t]==z){duplicate=1;break;}if(duplicate)continue;
   uint64_t c=base|sep(z);
   for(int keep=0;keep<4;keep++){
    if((keep==3&&extra<2)||(keep&&extra<1))continue;
    if((c|((keep&1)?se[i]:0)|((keep&2)?se[j]:0))!=low)continue;
    W child[MAX];memcpy(child,rest,nr*sizeof(W));int m=nr;
    if(keep&1)m=insert(child,m,a);
    if(keep&2)m=insert(child,m,b);
    m=insert(child,m,z);
    if(rec(child,m,k-1))return 1;
   }
  }
 }
 add(h);return 0;
}
static W hex(const char *s){W w=0;for(;*s;s++){int v=*s>='0'&&*s<='9'?*s-'0':*s>='a'&&*s<='f'?*s-'a'+10:*s>='A'&&*s<='F'?*s-'A'+10:-1;if(v>=0)w=(w<<4)|v;}return w;}
int main(void){
 int n,k;char b[4096];if(scanf("%d%d%d%lld",&n,&p,&k,&limit)!=4)return 2;
 if(n<1||n>8||p<1||p>64||k<0||k>17||limit<1){puts("toolarge");return 0;}
 full=p==64?~(W)0:(((W)1<<(2*p))-1);
 low=p==64?UINT64_MAX:((1ULL<<p)-1);goal=can((W)low);
 W in[8];for(int i=0;i<n;i++){if(scanf("%4095s",b)!=1)return 2;in[i]=can(hex(b)&full);}
 uint64_t cap=1024;while(cap<(uint64_t)limit*2&&cap<(1ULL<<25))cap<<=1;
 tm=cap-1;tab=calloc(cap,sizeof(uint64_t));if(!tab){puts("limit");return 0;}
 for(int mask=1;mask<(1<<n);mask++){
  W s[MAX];int m=0;uint64_t c=0;
  for(int i=0;i<n;i++)if(mask>>i&1){int dup=0;for(int j=0;j<m;j++)if(s[j]==in[i])dup=1;if(!dup&&in[i])m=insert(s,m,in[i]);c|=sep(in[i]);}
  if(c!=low||m-1>k)continue;
  if(rec(s,m,k)){puts("found");fprintf(stderr,"states=%lld\n",count);return 0;}
 }
 puts("none");fprintf(stderr,"states=%lld\n",count);return 0;
}

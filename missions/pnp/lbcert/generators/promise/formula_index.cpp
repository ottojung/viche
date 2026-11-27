/* Exact semantic formula-cost DP. This is a positive candidate index, not
   an exact DAG-cost solver. Independent promise replay for every record. */
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <vector>
#include <unordered_map>
#include <chrono>
using U=uint32_t;
struct Node{U a,b;uint8_t op;};
struct Gate{uint8_t op,a,b;};
static std::vector<uint8_t> cost;
static std::vector<Node> nodes;
static std::vector<std::vector<U>> levels;
static std::vector<U> inputs;
static int n,w,kmax,allow;
static U full;
static uint64_t pairs=0;
static void add(U v,int k,int op,U a,U b){
 if(cost[v]!=255)return;
 cost[v]=k;nodes[v]={a,b,(uint8_t)op};levels[k].push_back(v);
}
static int emit(U v,std::vector<Gate>& g,std::unordered_map<U,int>& memo){
 auto f=memo.find(v);if(f!=memo.end())return f->second;
 auto t=nodes[v];if(t.op==3)return t.a;
 int a=emit(t.a,g,memo),b=t.op==2?0:emit(t.b,g,memo);
 if(t.op<2&&a>b)std::swap(a,b);
 if(t.op<2&&a==b){memo[v]=a;return a;}
 for(unsigned i=0;i<g.size();i++)if(g[i].op==t.op&&g[i].a==a&&g[i].b==b){memo[v]=n+i;return n+i;}
 int r=n+g.size();g.push_back({t.op,(uint8_t)a,(uint8_t)b});memo[v]=r;return r;
}
static void wr(FILE*f,U x){if(fwrite(&x,4,1,f)!=1)abort();}
int main(int argc,char**argv){
 if(argc!=2||scanf("%d%d%d%d",&n,&w,&kmax,&allow)!=4)return 2;
 if(n<1||n>12||w<1||w>22||kmax<0||kmax>15||(allow!=0&&allow!=1))return 2;
 full=(1u<<w)-1;inputs.resize(n);cost.assign(full+1,255);nodes.resize(full+1);levels.resize(kmax+1);
 for(int i=0;i<n;i++){U v;if(scanf("%u",&v)!=1||v>full)return 2;inputs[i]=v;add(v,0,3,i,0);}
 auto start=std::chrono::steady_clock::now();
 for(int k=1;k<=kmax;k++){
  if(allow)for(auto a:levels[k-1])add(full^a,k,2,a,0);
  for(int i=0;i<=(k-1)/2;i++){
   int j=k-1-i;
   for(size_t ai=0;ai<levels[i].size();ai++){
    U a=levels[i][ai];size_t bj=i==j?ai+1:0;
    for(;bj<levels[j].size();bj++){
     U b=levels[j][bj];pairs++;add(a&b,k,0,a,b);add(a|b,k,1,a,b);
    }
   }
  }
  fprintf(stderr,"depth %d new %zu pairs %llu seconds %.3f\n",k,levels[k].size(),(unsigned long long)pairs,std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count());fflush(stderr);
 }
 FILE*out=fopen(argv[1],"wb+");if(!out)return 2;
 if(fwrite("VICHER01",1,8,out)!=8)abort();wr(out,n);wr(out,w);wr(out,kmax);wr(out,allow?3:0);
 for(auto x:inputs)wr(out,x);
 long index_start=ftell(out);
 std::vector<U> index(full+1);if(fseek(out,(long)index.size()*4,SEEK_CUR))abort();
 size_t count=0;
 for(auto&level:levels)for(auto t:level){
  std::vector<Gate> g;std::unordered_map<U,int> memo;
  int root=emit(t,g,memo);std::vector<U> v=inputs;
  for(auto x:g)v.push_back(x.op==2?full^v[x.a]:x.op?v[x.a]|v[x.b]:v[x.a]&v[x.b]);
  if(v[root]!=t||g.size()>(unsigned)kmax)abort();
  long pos=ftell(out);if(pos<=0||(unsigned long)pos>UINT32_MAX-100)abort();
  index[t]=pos;uint8_t hdr[2]={(uint8_t)g.size(),(uint8_t)root};
  if(fwrite(hdr,1,2,out)!=2||fwrite(g.data(),sizeof(Gate),g.size(),out)!=g.size())abort();count++;
 }
 if(fseek(out,index_start,SEEK_SET)||fwrite(index.data(),4,index.size(),out)!=index.size()||fclose(out))abort();
 fprintf(stderr,"DONE %zu witnesses\n",count);
}

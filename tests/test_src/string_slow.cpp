#include<iostream>
#include<cstdio>
#include<string>
#include<cstring>
#include<vector>
#include<cmath>
#include<queue>
#include<stack>
#include<map>
#include<set>
#include<algorithm>
using namespace std;
const int maxn=250010;
const int SIGMA_SIZE=26;
struct SAM_Node
{
    SAM_Node *par,*next[SIGMA_SIZE];
    int len,id,pos;
    SAM_Node(){}
    SAM_Node(int _len)
    {
        par=0;
        len=_len;
        memset(next,0,sizeof(next));
    }
};
SAM_Node node[maxn*2],*root,*last;
int SAM_size;
SAM_Node *newSAM_Node(int len)
{
    node[SAM_size]=SAM_Node(len);
    node[SAM_size].id=SAM_size;
    return &node[SAM_size++];
}
SAM_Node *newSAM_Node(SAM_Node *p)
{
    node[SAM_size]=*p;
    node[SAM_size].id=SAM_size;
    return &node[SAM_size++];
}
void SAM_init()
{
    SAM_size=0;
    root=last=newSAM_Node(0);
    node[0].pos=0;
}
void SAM_add(int x,int len)
{
    SAM_Node *p=last,*np=newSAM_Node(p->len+1);
    np->pos=len;
    last=np;
    while(p&&!p->next[x])
    {
        p->next[x]=np;
        p=p->par;
    }
    if(!p)
    {
        np->par=root;
        return ;
    }
    SAM_Node *q=p->next[x];
    if(q->len==p->len+1)
    {
        np->par=q;
        return ;
    }
    SAM_Node *nq=newSAM_Node(q);
    nq->len=p->len+1;
    q->par=nq;
    np->par=nq;
    while(p&&p->next[x]==q)
    {
        p->next[x]=nq;
        p=p->par;
    }
}
void SAM_build(char *s)
{
    SAM_init();
    int le=strlen(s);
    for(int i=0;i<le;i++)
        SAM_add(s[i]-'a',i+1);
}
int solve(char* str1,char* str2,int x)
{
    SAM_build(str1);
    SAM_Node *tmp=root;
    int le=strlen(str2);
    int cnt=0,ans=0;
    for(int i=0;i<le;i++)
    {
        int c=str2[i]-'a';
        if(tmp->next[c])
            tmp=tmp->next[c],cnt++;
        else
        {
            while(tmp&&!tmp->next[c])
                tmp=tmp->par;
            if(!tmp)
                tmp=root,cnt=0;
            else
            {
                cnt=tmp->len+1;
                tmp=tmp->next[c];
            }
        }
        if (cnt >= x) return i+1;
    }
    return -1;
}
char s[250010]={},s1[11][250010]={};
int main(){
    scanf("%s",s);
    int n,leng,l,r,ans;
    leng=strlen(s);
    cin >> n;
    for (int i=1;i<=n;i++) scanf("%s",s1[i]);
    r=leng/n; l=0; ans=(l+r)/2;
    while (l<r){
        int t=1,x=0;
        for (int i=1;i<=n;i++){
            int y=solve(s1[i],s+x,ans);
            if (y==-1) t=0;
            else x+=y;
            //cout << ans << " " << x << endl;
        }
        if (x>leng) t=0;
        if (t){
            l=ans;
        }
        else{
            r=ans-1;
        }
        ans=(l+r+1)/2;
        //cout << l << " " << r << endl;
    }
    if (ans==0) cout << -1 << endl;
    else cout << ans << endl;
}
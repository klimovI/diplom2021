void main() {
  int i,n=5;
  double x[7],y[7],a[7],b[7],c[7],S[7],AO[7],OO[7],h=M_PI/4,
  x1=M_PI/8, x2=3*M_PI/8, x3=5*M_PI/8, x4=7*M_PI/8,
  y1=sin(x1), y2=sin(x2), y3=sin(x3), y4=sin(x4);


  for(i=0;i<5;i++) x[i]=i*h;

  x[-1]=x[0];
  x[5]=x[4];


  for(i=0;i<5;i++) y[i]=sin(x[i]);

  y[-1]=(y[1]-y[0])/(x[1]-x[0]);
  y[5]=(y[4]-y[3])/(x[4]-x[3]);

  for(i=0;i<5;i++) a[i]=y[i];

  b[0]=y[-1];

  for(i=1;i<6;i++) b[i]=2*(y[i]-y[i-1])/h-b[i-1];

  b[6]=y[5];

  for(i=1;i<6;i++) c[i-1]=(b[i]-b[i-1])/2/h;

  c[5]=(b[n+1]-b[n])/2/h;


  S[1]=a[1]+b[1]*(x1-x[1])+c[1]*(x1-x[1])*(x1-x[1]);
  AO[1]=fabs(S[1]-y1); OO[1]=AO[1]/y1*100;
  S[2]=a[2]+b[2]*(x2-x[2])+c[2]*(x2-x[2])*(x2-x[2]);
  AO[2]=fabs(S[2]-y2); OO[2]=AO[2]/y2*100;
  S[3]=a[3]+b[3]*(x3-x[3])+c[3]*(x3-x[3])*(x3-x[3]);
  AO[3]=fabs(S[3]-y3); OO[3]=AO[3]/y3*100;
  S[4]=a[4]+b[4]*(x4-x[4])+c[4]*(x4-x[4])*(x4-x[4]);
  AO[4]=fabs(S[4]-y4); OO[4]=AO[4]/y4*100;
  
  for(i=1;i<5;i++)
  printf(" S[%d] %3.5lf AO[%d] %3.5lf OO[%d] %3.5lf\n",
  i,S[i],i,AO[i],i,OO[i]);
  getch();
}
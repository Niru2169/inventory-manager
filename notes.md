CR decomposition
C*RREF where C contains pivotal og columns

Diagonalization
A = PDP^-1 
[P,D]=eig(A)

LU
take an elementary matrix and an identity matrix of same dimensions
try to make the elementary matrix a lower triangular matrix
perform the same operations to the identity matrix, it will become an upper triangular matrix

Spectral
A = QVQ'
Q = orthogonalized(eigenvectors(A))
V = diagonalmatrix(eigenvalues(A))

SVD
A=USV'
U = eigenvectors(AA')
S = sqrt(eigenvalues(AA'))
V' = eigenvectors(A'A)

Pseudoinv (I'll use `)
A` = VS`U^-1
to find S`, take S' and take multiplicative inverse of every element

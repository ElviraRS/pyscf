import numpy as np
import pyscf.dft

def eval_ao(cell, coords, kpt=None, isgga=False, relativity=0, bastart=0,
            bascount=None, non0tab=None, verbose=None):
    '''Collocate AO crystal orbitals (opt. gradients) on the real-space grid.

    With the optional kpt arguments, returns the pair of 
    sin, cos crystal orbitals at that kpt. 

    (kpt==0 denotes Gamma pt, returns values of only one set)

    Args:
        cell : instance of :class:`Cell`

        coords : (nx*ny*nz, 3) ndarray
            The real-space grid point coordinates.

    Returns:
        aoR : ([4,] nx*ny*nz, nao=cell.nao_nr()) ndarray 
            The value of the AO crystal orbitals on the real-space grid. If
            isgga=True, also contains the value of the orbitals gradient in the
            x, y, and z directions.

    See Also:
        pyscf.dft.numint.eval_ao

    '''  
    if kpt is None:
        kpt = np.zeros([3,1])

    nimgs = cell.nimgs
    Ts = [[i,j,k] for i in range(-nimgs[0],nimgs[0]+1)
                  for j in range(-nimgs[1],nimgs[1]+1)
                  for k in range(-nimgs[2],nimgs[2]+1)
                  if i**2+j**2+k**2 <= 1./3*np.dot(nimgs,nimgs)]
    
    nao = cell.nao_nr()
    if isgga:
        aoR = np.zeros([4,coords.shape[0], nao], np.complex128)
    else:
        aoR = np.zeros([coords.shape[0], nao], np.complex128)

    for T in Ts:
        L = np.dot(cell.h, T)
        aoR += (np.exp(1j*np.dot(kpt.T,L)) *
                pyscf.dft.numint.eval_ao(cell, coords-L,
                                         isgga, relativity, 
                                         bastart, bascount, 
                                         non0tab, verbose))
    return aoR

def eval_rho(mol, ao, dm, non0tab=None, 
             isgga=False, verbose=None):
    '''Collocate the *real* density (opt. gradients) on the real-space grid.

    Args:
        mol : instance of :class:`Mole` or :class:`Cell`

        ao : ([4,] nx*ny*nz, nao=2*cell.nao_nr()) ndarray 
            The value of the AO crystal orbitals on the real-space grid. If
            isgga=True, also contains the value of the gradient in the x, y,
            and z directions.

    Returns:
        rho : ([4,] nx*ny*nz) ndarray
            The value of the density on the real-space grid. If isgga=True,
            also contains the value of the gradient in the x, y, and z
            directions.

    See Also:
        pyscf.dft.numint.eval_rho

    '''  
    import numpy
    from pyscf.dft.numint import _dot_ao_dm, BLKSIZE

    if isgga:
        ngrids, nao = ao[0].shape
    else:
        ngrids, nao = ao.shape

    if non0tab is None:
        non0tab = numpy.ones(((ngrids+BLKSIZE-1)//BLKSIZE,mol.nbas),
                             dtype=numpy.int8)

    #if ao[0].dtype==numpy.complex128: # complex orbitals
    if True:
        dm_re = numpy.ascontiguousarray(dm.real)
        dm_im = numpy.ascontiguousarray(dm.imag)

        if isgga:
            rho = numpy.empty((4,ngrids))
            ao_re = numpy.ascontiguousarray(ao[0].real)
            ao_im = numpy.ascontiguousarray(ao[0].imag)
            ao_re = numpy.ascontiguousarray(ao[0].real)
            ao_im = numpy.ascontiguousarray(ao[0].imag)

            # DM * ket: e.g. ir denotes dm_im | ao_re >
            c0_rr = _dot_ao_dm(mol, ao_re, dm_re, nao, ngrids, non0tab)
            c0_ri = _dot_ao_dm(mol, ao_im, dm_re, nao, ngrids, non0tab)
            c0_ir = _dot_ao_dm(mol, ao_re, dm_im, nao, ngrids, non0tab)
            c0_ii = _dot_ao_dm(mol, ao_im, dm_im, nao, ngrids, non0tab)

            # bra * DM
            rho[0] = (numpy.einsum('pi,pi->p', ao_im, c0_ri) +
                      numpy.einsum('pi,pi->p', ao_re, c0_rr) +
                      numpy.einsum('pi,pi->p', ao_im, c0_ir) -
                      numpy.einsum('pi,pi->p', ao_re, c0_ii))

            for i in range(1, 4):
                ao_re = numpy.ascontiguousarray(ao[i].real)
                ao_im = numpy.ascontiguousarray(ao[i].imag)

                c1_rr = _dot_ao_dm(mol, ao_re, dm_re, nao, ngrids, non0tab)
                c1_ri = _dot_ao_dm(mol, ao_im, dm_re, nao, ngrids, non0tab)
                c1_ir = _dot_ao_dm(mol, ao_re, dm_im, nao, ngrids, non0tab)
                c1_ii = _dot_ao_dm(mol, ao_im, dm_im, nao, ngrids, non0tab)

                rho[i] = (numpy.einsum('pi,pi->p', ao_im, c1_ri) +
                          numpy.einsum('pi,pi->p', ao_re, c1_rr) +
                          numpy.einsum('pi,pi->p', ao_im, c1_ir) -
                          numpy.einsum('pi,pi->p', ao_re, c1_ii)) * 2 # *2 for +c.c.       
        else:
            ao_re = numpy.ascontiguousarray(ao.real)
            ao_im = numpy.ascontiguousarray(ao.imag)
            # DM * ket: e.g. ir denotes dm_im | ao_re >
            
            c0_rr = _dot_ao_dm(mol, ao_re, dm_re, nao, ngrids, non0tab)
            c0_ri = _dot_ao_dm(mol, ao_im, dm_re, nao, ngrids, non0tab)
            c0_ir = _dot_ao_dm(mol, ao_re, dm_im, nao, ngrids, non0tab)
            c0_ii = _dot_ao_dm(mol, ao_im, dm_im, nao, ngrids, non0tab)
            # bra * DM
            rho = (numpy.einsum('pi,pi->p', ao_im, c0_ri) +
                   numpy.einsum('pi,pi->p', ao_re, c0_rr) +
                   numpy.einsum('pi,pi->p', ao_im, c0_ir) -
                   numpy.einsum('pi,pi->p', ao_re, c0_ii))
                                    
    else:
        rho = pyscf.dft.numint.eval_rho(mol, ao, dm, non0tab, isgga, verbose)
    
    return rho

def eval_mat(mol, ao, weight, rho, vrho, vsigma=None, non0tab=None,
             isgga=False, verbose=None):
    '''Calculate the XC potential AO matrix.

    Args:
        mol : instance of :class:`Mole` or :class:`Cell`

        ao : ([4,] nx*ny*nz, nao=cell.nao_nr()) ndarray 
            The value of the AO crystal orbitals on the real-space grid. If
            isgga=True, also contains the value of the gradient in the x, y,
            and z directions.

    Returns:
        rho : ([4,] nx*ny*nz) ndarray
            The value of the density on the real-space grid. If isgga=True,
            also contains the value of the gradient in the x, y, and z
            directions.
    
    See Also:
        pyscf.dft.numint.eval_mat

    '''
    from pyscf.dft.numint import BLKSIZE, _dot_ao_ao
    import numpy

    if isgga:
        ngrids, nao = ao[0].shape
    else:
        ngrids, nao = ao.shape

    if non0tab is None:
        non0tab = numpy.ones(((ngrids+BLKSIZE-1)//BLKSIZE,mol.nbas),
                             dtype=numpy.int8)

    if ao[0].dtype==numpy.complex128:
        if isgga:
            assert(vsigma is not None and rho.ndim==2)
            #wv = weight * vsigma * 2
            #aow  = numpy.einsum('pi,p->pi', ao[1], rho[1]*wv)
            #aow += numpy.einsum('pi,p->pi', ao[2], rho[2]*wv)
            #aow += numpy.einsum('pi,p->pi', ao[3], rho[3]*wv)
            #aow += numpy.einsum('pi,p->pi', ao[0], .5*weight*vrho)
            wv = numpy.empty_like(rho)
            wv[0]  = weight * vrho * .5
            wv[1:] = rho[1:] * (weight * vsigma * 2)
            aow = numpy.einsum('npi,np->pi', ao, wv)

            ao_re = numpy.ascontiguousarray(ao[0].real)
            ao_im = numpy.ascontiguousarray(ao[0].imag)

            aow_re = numpy.ascontiguousarray(aow.real)
            aow_im = numpy.ascontiguousarray(aow.imag)

        else:
            # *.5 because return mat + mat.T
            #:aow = numpy.einsum('pi,p->pi', ao, .5*weight*vrho)
            ao_re = numpy.ascontiguousarray(ao.real)
            ao_im = numpy.ascontiguousarray(ao.imag)

            aow_re = ao_re * (.5*weight*vrho).reshape(-1,1)
            aow_im = ao_im * (.5*weight*vrho).reshape(-1,1)
            #mat = pyscf.lib.dot(ao.T, aow)

        mat_re = _dot_ao_ao(mol, ao_re, aow_re, nao, ngrids, non0tab)
        mat_re += _dot_ao_ao(mol, ao_im, aow_im, nao, ngrids, non0tab)
        mat_im = _dot_ao_ao(mol, ao_re, aow_im, nao, ngrids, non0tab)
        mat_im -= _dot_ao_ao(mol, ao_im, aow_re, nao, ngrids, non0tab)

        mat = mat_re + 1j*mat_im

        # print "MATRIX", mat.dtype
        return mat + mat.T.conj()
        
    else:
        return pyscf.dft.numint.eval_mat(mol, ao, 
                                         weight, rho, vrho, 
                                         vsigma=None, non0tab=None,
                                         isgga=False, verbose=None)


class _NumInt(pyscf.dft.numint._NumInt):
    '''Generalization of pyscf's _NumInt class for a single k-pt shift and
    periodic images.'''

    def __init__(self, kpt=None):
        pyscf.dft.numint._NumInt.__init__(self)
        self.kpt = kpt

    def eval_ao(self, mol, coords, isgga=False, relativity=0, bastart=0,
                bascount=None, non0tab=None, verbose=None):
        return eval_ao(mol, coords, self.kpt, isgga, relativity, bastart, 
                       bascount, non0tab, verbose)

    def eval_rho(self, mol, ao, dm, non0tab=None, isgga=False, verbose=None):
        return eval_rho(mol, ao, dm, non0tab, isgga, verbose)

    def eval_rho2(self, mol, ao, dm, non0tab=None, isgga=False, verbose=None):
        raise NotImplementedError

    def nr_rks(self, mol, grids, x_id, c_id, dms, hermi=1,
               max_memory=2000, verbose=None):
        '''
        Use slow function in numint, which only calls eval_rho, eval_mat.
        Faster function uses eval_rho2 which is not yet implemented.
        '''
        return pyscf.dft.numint.nr_rks_vxc(self, mol, grids, x_id, c_id, dms, 
                                           spin=0, relativity=0, hermi=1,
                                           max_memory=max_memory, verbose=verbose)

    def nr_uks(self, mol, grids, x_id, c_id, dms, hermi=1,
               max_memory=2000, verbose=None):
        raise NotImplementedError

    def eval_mat(self, mol, ao, weight, rho, vrho, vsigma=None, non0tab=None,
                 isgga=False, verbose=None):
        # use local function for complex eval_mat
        return eval_mat(mol, ao, weight, rho, vrho, vsigma, non0tab,
                        isgga, verbose)


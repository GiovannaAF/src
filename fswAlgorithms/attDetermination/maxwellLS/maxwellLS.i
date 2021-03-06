/*
 ISC License
 
 Copyright (c) 2016-2018, Autonomous Vehicle Systems Lab, University of Colorado at Boulder
 
 Permission to use, copy, modify, and/or distribute this software for any
 purpose with or without fee is hereby granted, provided that the above
 copyright notice and this permission notice appear in all copies.
 
 THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 
 */
%module maxwellLS
%{
#include "maxwellLS.h"
    %}

%include "swig_conly_data.i"
%constant void Update_maxwellLS(void*, uint64_t, uint64_t);
%ignore Update_maxwellLS;
%constant void SelfInit_maxwellLS(void*, uint64_t);
%ignore SelfInit_maxwellLS;
%constant void CrossInit_maxwellLS(void*, uint64_t);
%ignore CrossInit_maxwellLS;
%constant void Reset_maxwellLS(void*, uint64_t, uint64_t);
%ignore Reset_maxwellLS;

STRUCTASLIST(CSSUnitConfigFswMsg)
GEN_SIZEOF(CSSConfigFswMsg);
GEN_SIZEOF(CSSUnitConfigFswMsg);
GEN_SIZEOF(maxwellLSConfig);
%include "maxwellLS.h"
%include "simFswInterfaceMessages/navAttIntMsg.h"
%include "simFswInterfaceMessages/sunpointIntMsg.h"
%include "../../fswMessages/cssConfigFswMsg.h"
%include "../../fswMessages/cssUnitConfigFswMsg.h"

%pythoncode %{
    import sys
    protectAllClasses(sys.modules[__name__])
    %}


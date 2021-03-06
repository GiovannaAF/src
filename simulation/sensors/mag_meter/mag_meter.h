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

#ifndef MAG_METER_H
#define MAG_METER_H

#include <vector>
#include "_GeneralModuleFiles/sys_model.h"
#include "utilities/gauss_markov.h"
#include "simMessages/scPlusStatesSimMsg.h"
#include "simMessages/spiceTimeSimMsg.h"
#include "simFswInterfaceMessages/MagMeterIntMsg.h"
#include <Eigen/Dense>
#include "../simulation/utilities/avsEigenMRP.h"


class MagMeter: public SysModel {
public:
    MagMeter();
    ~MagMeter();
    
    bool LinkMessages();
    void UpdateState(uint64_t CurrentSimNanos);
    void SelfInit();
    void CrossInit();
    void readInputMessages();
    void writeOutputMessages(uint64_t Clock);
    void computeMagField(uint64_t CurrentSimNanos);
    void computeSensorErrors();
    void applySensorErrors();

public:


    uint64_t sensorTimeTag;            //!< [ns] Current time tag for sensor out
    std::string inputStateMessage;    //!< [-] String for the input state message
    std::string outputStateMessage;   //!< [-] String for the output state message
    bool messagesLinked;              //!< [-] Indicator for whether inputs bound
    Eigen::Matrix3d PMatrix;      //!< [-] Covariance matrix used to perturb state
    Eigen::Vector3d walkBounds;   //!< [-] "3-sigma" errors to permit for states
    Eigen::Vector3d navErrors;    //!< [-] Current navigation errors applied to truth
    Eigen::Vector3d senBias;
    uint64_t OutputBufferCount;       //!< [-] Count on the number of output message buffers
    MagMeterIntMsg sensedValues;//!< [-] total measurement including perturbations
    SCPlusStatesSimMsg scState;      //!< [-] Module variable where the input State Data message is stored
    double inclination;
    double orbitRadius;




private:
    Eigen::Matrix3d AMatrix;            //!< [-] AMatrix that we use for error propagation
    int64_t inputStateID;               //!< [-] Connection to input state message
    int64_t outputStateID;              //!< [-] Connection to outgoing state message
    uint64_t PreviousTime;              /// -- Timestamp from previous frame
    GaussMarkov errorModel;             //!< [-] Gauss-markov error states
    Eigen::Vector3d mag_bf_out;
    Eigen::Vector3d mag_hill_out;
};

#endif

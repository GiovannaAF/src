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

#ifndef _SUNLINE_UKF_H_
#define _SUNLINE_UKF_H_

#include "messaging/static_messaging.h"
#include <stdint.h>
#include "simFswInterfaceMessages/navAttIntMsg.h"
#include "simFswInterfaceMessages/cssArraySensorIntMsg.h"
#include "fswMessages/vehicleConfigFswMsg.h"
#include "fswMessages/sunlineFilterFswMsg.h"
#include "fswMessages/cssConfigFswMsg.h"


/*! \addtogroup ADCSAlgGroup
 * @{
 */

/*!@brief Data structure for CSS Switch unscented kalman filter estimator. Please see the _Documentation folder for details on how this Kalman Filter Functions.
 */
typedef struct {
    char navStateOutMsgName[MAX_STAT_MSG_LENGTH]; /*!< The name of the output message*/
    char filtDataOutMsgName[MAX_STAT_MSG_LENGTH]; /*!< The name of the output filter data message*/
    char cssDataInMsgName[MAX_STAT_MSG_LENGTH]; /*!< The name of the Input message*/
    char cssConfigInMsgName[MAX_STAT_MSG_LENGTH]; /*!< [-] The name of the CSS configuration message*/
    
	int numStates;                /*!< [-] Number of states for this filter*/
	int countHalfSPs;             /*!< [-] Number of sigma points over 2 */
	int numObs;                   /*!< [-] Number of measurements this cycle */
	double beta;                  /*!< [-] Beta parameter for filter */
	double alpha;                 /*!< [-] Alpha parameter for filter*/
	double kappa;                 /*!< [-] Kappa parameter for filter*/
	double lambdaVal;             /*!< [-] Lambda parameter for filter*/
	double gamma;                 /*!< [-] Gamma parameter for filter*/
    double qObsVal;               /*!< [-] CSS instrument noise parameter*/

	double dt;                     /*!< [s] seconds since last data epoch */
	double timeTag;                /*!< [s]  Time tag for statecovar/etc */

    double bVec_B[SKF_N_STATES_HALF];       /*!< [-] current vector of the b frame used to make frame */
    double switchTresh;             /*!< [-]  Threshold for switching frames */
    
    double state[SKF_N_STATES_SWITCH];        /*!< [-] State estimate for time TimeTag*/
    
	double wM[2 * SKF_N_STATES_SWITCH + 1]; /*!< [-] Weighting vector for sigma points*/
	double wC[2 * SKF_N_STATES_SWITCH + 1]; /*!< [-] Weighting vector for sigma points*/

	double sBar[SKF_N_STATES_SWITCH*SKF_N_STATES_SWITCH];         /*!< [-] Time updated covariance */
	double covar[SKF_N_STATES_SWITCH*SKF_N_STATES_SWITCH];        /*!< [-] covariance */
    double xBar[SKF_N_STATES_SWITCH];            /*! [-] Current mean state estimate*/

	double obs[MAX_N_CSS_MEAS];          /*!< [-] Observation vector for frame*/
	double yMeas[MAX_N_CSS_MEAS*(2*SKF_N_STATES_SWITCH+1)];        /*!< [-] Measurement model data */
    double postFits[MAX_N_CSS_MEAS];  /*!< [-] PostFit residuals */
    
	double SP[(2*SKF_N_STATES_SWITCH+1)*SKF_N_STATES_SWITCH];     /*!< [-]    sigma point matrix */

	double qNoise[SKF_N_STATES_SWITCH*SKF_N_STATES_SWITCH];       /*!< [-] process noise matrix */
	double sQnoise[SKF_N_STATES_SWITCH*SKF_N_STATES_SWITCH];      /*!< [-] cholesky of Qnoise */

	double qObs[MAX_N_CSS_MEAS*MAX_N_CSS_MEAS];  /*!< [-] Maximally sized obs noise matrix*/
    
    double cssNHat_B[MAX_NUM_CSS_SENSORS*3];     /*!< [-] CSS normal vectors converted over to body*/
    double CBias[MAX_NUM_CSS_SENSORS];       /*!< [-] CSS individual calibration coefficients */

    uint32_t numActiveCss;   /*!< -- Number of currently active CSS sensors*/
    uint32_t numCSSTotal;    /*!< [-] Count on the number of CSS we have on the spacecraft*/
    double sensorUseThresh;  /*!< -- Threshold below which we discount sensors*/
	NavAttIntMsg outputSunline;   /*!< -- Output sunline estimate data */
    CSSArraySensorIntMsg cssSensorInBuffer; /*!< [-] CSS sensor data read in from message bus*/

    int32_t navStateOutMsgId;     /*!< -- ID for the outgoing body estimate message*/
    int32_t filtDataOutMsgId;   /*!< [-] ID for the filter data output message*/
    int32_t cssDataInMsgId;      /*!< -- ID for the incoming CSS sensor message*/
    int32_t cssConfigInMsgId;   /*!< [-] ID associated with the CSS configuration data*/
}SunlineSuKFConfig;

#ifdef __cplusplus
extern "C" {
#endif
    
    void SelfInit_sunlineSuKF(SunlineSuKFConfig *ConfigData, uint64_t moduleID);
    void CrossInit_sunlineSuKF(SunlineSuKFConfig *ConfigData, uint64_t moduleID);
    void Update_sunlineSuKF(SunlineSuKFConfig *ConfigData, uint64_t callTime,
        uint64_t moduleID);
	void Reset_sunlineSuKF(SunlineSuKFConfig *ConfigData, uint64_t callTime,
		uint64_t moduleID);
	void sunlineSuKFTimeUpdate(SunlineSuKFConfig *ConfigData, double updateTime);
    void sunlineSuKFMeasUpdate(SunlineSuKFConfig *ConfigData, double updateTime);
	void sunlineStateProp(double *stateInOut,  double *b_vec, double dt);
    void sunlineSuKFMeasModel(SunlineSuKFConfig *ConfigData);
    void sunlineSuKFComputeDCM_BS(double sunheading[SKF_N_STATES_HALF], double bVec[SKF_N_STATES_HALF], double *dcm);
    void sunlineSuKFSwitch(double *bVec_B, double *states, double *covar);

#ifdef __cplusplus
}
#endif

/*! @} */

#endif

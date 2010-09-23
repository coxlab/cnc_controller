/*M///////////////////////////////////////////////////////////////////////////////////////
//
//  IMPORTANT: READ BEFORE DOWNLOADING, COPYING, INSTALLING OR USING.
//
//  By downloading, copying, installing or using the software you agree to this license.
//  If you do not agree to this license, do not download, install,
//  copy or use the software.
//
//
//                           License Agreement
//                For Open Source Computer Vision Library
//
// Copyright (C) 2000-2008, Intel Corporation, all rights reserved.
// Copyright (C) 2009, Willow Garage Inc., all rights reserved.
// Third party copyrights are property of their respective owners.
//
// Redistribution and use in source and binary forms, with or without modification,
// are permitted provided that the following conditions are met:
//
//   * Redistribution's of source code must retain the above copyright notice,
//     this list of conditions and the following disclaimer.
//
//   * Redistribution's in binary form must reproduce the above copyright notice,
//     this list of conditions and the following disclaimer in the documentation
//     and/or other materials provided with the distribution.
//
//   * The name of the copyright holders may not be used to endorse or promote products
//     derived from this software without specific prior written permission.
//
// This software is provided by the copyright holders and contributors "as is" and
// any express or implied warranties, including, but not limited to, the implied
// warranties of merchantability and fitness for a particular purpose are disclaimed.
// In no event shall the Intel Corporation or contributors be liable for any direct,
// indirect, incidental, special, exemplary, or consequential damages
// (including, but not limited to, procurement of substitute goods or services;
// loss of use, data, or profits; or business interruption) however caused
// and on any theory of liability, whether in contract, strict liability,
// or tort (including negligence or otherwise) arising in any way out of
// the use of this software, even if advised of the possibility of such damage.
//
//M*/

//#include "cuda_shared.hpp"
#include "opencv2/gpu/devmem2d.hpp"
#include "safe_call.hpp"
static inline int divUp(int a, int b) { return (a % b == 0) ? a/b : a/b + 1; }



using namespace cv::gpu;

//////////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////// Streeo BM ////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////////////////////

#define ROWSperTHREAD 21     // the number of rows a thread will process

namespace stereobm_gpu
{

#define BLOCK_W 128          // the thread block width (464)
#define N_DISPARITIES 8

#define STEREO_MIND 0                    // The minimum d range to check
#define STEREO_DISP_STEP N_DISPARITIES   // the d step, must be <= 1 to avoid aliasing

__constant__ unsigned int* cminSSDImage;
__constant__ size_t cminSSD_step;
__constant__ int cwidth;
__constant__ int cheight;

__device__ int SQ(int a)
{
    return a * a;
}

template<int RADIUS>
__device__ unsigned int CalcSSD(volatile unsigned int *col_ssd_cache, volatile unsigned int *col_ssd)
{	
    unsigned int cache = 0;
    unsigned int cache2 = 0;

    for(int i = 1; i <= RADIUS; i++)
        cache += col_ssd[i];

    col_ssd_cache[0] = cache;

    __syncthreads();

    if (threadIdx.x < BLOCK_W - RADIUS)
        cache2 = col_ssd_cache[RADIUS];
    else
        for(int i = RADIUS + 1; i < (2 * RADIUS + 1); i++)
            cache2 += col_ssd[i];

    return col_ssd[0] + cache + cache2;
}

template<int RADIUS>
__device__ uint2 MinSSD(volatile unsigned int *col_ssd_cache, volatile unsigned int *col_ssd)
{
    unsigned int ssd[N_DISPARITIES];

    //See above:  #define COL_SSD_SIZE (BLOCK_W + 2 * RADIUS)
    ssd[0] = CalcSSD<RADIUS>(col_ssd_cache, col_ssd + 0 * (BLOCK_W + 2 * RADIUS));
	__syncthreads();
    ssd[1] = CalcSSD<RADIUS>(col_ssd_cache, col_ssd + 1 * (BLOCK_W + 2 * RADIUS));
	__syncthreads();
    ssd[2] = CalcSSD<RADIUS>(col_ssd_cache, col_ssd + 2 * (BLOCK_W + 2 * RADIUS));
	__syncthreads();
    ssd[3] = CalcSSD<RADIUS>(col_ssd_cache, col_ssd + 3 * (BLOCK_W + 2 * RADIUS));
	__syncthreads();
    ssd[4] = CalcSSD<RADIUS>(col_ssd_cache, col_ssd + 4 * (BLOCK_W + 2 * RADIUS));
	__syncthreads();
    ssd[5] = CalcSSD<RADIUS>(col_ssd_cache, col_ssd + 5 * (BLOCK_W + 2 * RADIUS));
	__syncthreads();
    ssd[6] = CalcSSD<RADIUS>(col_ssd_cache, col_ssd + 6 * (BLOCK_W + 2 * RADIUS));
	__syncthreads();
    ssd[7] = CalcSSD<RADIUS>(col_ssd_cache, col_ssd + 7 * (BLOCK_W + 2 * RADIUS));

    int mssd = min(min(min(ssd[0], ssd[1]), min(ssd[4], ssd[5])), min(min(ssd[2], ssd[3]), min(ssd[6], ssd[7])));

    int bestIdx = 0;
    for (int i = 0; i < N_DISPARITIES; i++)
    {
        if (mssd == ssd[i])
            bestIdx = i;
    }

    return make_uint2(mssd, bestIdx);
}

template<int RADIUS>
__device__ void StepDown(int idx1, int idx2, unsigned char* imageL, unsigned char* imageR, int d, volatile unsigned int *col_ssd)
{
    unsigned char leftPixel1;
    unsigned char leftPixel2;
    unsigned char rightPixel1[8];
    unsigned char rightPixel2[8];
    unsigned int diff1, diff2;

    leftPixel1 = imageL[idx1];
    leftPixel2 = imageL[idx2];

    idx1 = idx1 - d;
    idx2 = idx2 - d;

    rightPixel1[7] = imageR[idx1 - 7];
    rightPixel1[0] = imageR[idx1 - 0];
    rightPixel1[1] = imageR[idx1 - 1];
    rightPixel1[2] = imageR[idx1 - 2];
    rightPixel1[3] = imageR[idx1 - 3];
    rightPixel1[4] = imageR[idx1 - 4];
    rightPixel1[5] = imageR[idx1 - 5];
    rightPixel1[6] = imageR[idx1 - 6];

    rightPixel2[7] = imageR[idx2 - 7];
    rightPixel2[0] = imageR[idx2 - 0];
    rightPixel2[1] = imageR[idx2 - 1];
    rightPixel2[2] = imageR[idx2 - 2];
    rightPixel2[3] = imageR[idx2 - 3];
    rightPixel2[4] = imageR[idx2 - 4];
    rightPixel2[5] = imageR[idx2 - 5];
    rightPixel2[6] = imageR[idx2 - 6];

    //See above:  #define COL_SSD_SIZE (BLOCK_W + 2 * RADIUS)
    diff1 = leftPixel1 - rightPixel1[0];
    diff2 = leftPixel2 - rightPixel2[0];
    col_ssd[0 * (BLOCK_W + 2 * RADIUS)] += SQ(diff2) - SQ(diff1);

    diff1 = leftPixel1 - rightPixel1[1];
    diff2 = leftPixel2 - rightPixel2[1];
    col_ssd[1 * (BLOCK_W + 2 * RADIUS)] += SQ(diff2) - SQ(diff1);

    diff1 = leftPixel1 - rightPixel1[2];
    diff2 = leftPixel2 - rightPixel2[2];
    col_ssd[2 * (BLOCK_W + 2 * RADIUS)] += SQ(diff2) - SQ(diff1);

    diff1 = leftPixel1 - rightPixel1[3];
    diff2 = leftPixel2 - rightPixel2[3];
    col_ssd[3 * (BLOCK_W + 2 * RADIUS)] += SQ(diff2) - SQ(diff1);

    diff1 = leftPixel1 - rightPixel1[4];
    diff2 = leftPixel2 - rightPixel2[4];
    col_ssd[4 * (BLOCK_W + 2 * RADIUS)] += SQ(diff2) - SQ(diff1);

    diff1 = leftPixel1 - rightPixel1[5];
    diff2 = leftPixel2 - rightPixel2[5];
    col_ssd[5 * (BLOCK_W + 2 * RADIUS)] += SQ(diff2) - SQ(diff1);

    diff1 = leftPixel1 - rightPixel1[6];
    diff2 = leftPixel2 - rightPixel2[6];
    col_ssd[6 * (BLOCK_W + 2 * RADIUS)] += SQ(diff2) - SQ(diff1);

    diff1 = leftPixel1 - rightPixel1[7];
    diff2 = leftPixel2 - rightPixel2[7];
    col_ssd[7 * (BLOCK_W + 2 * RADIUS)] += SQ(diff2) - SQ(diff1);
}

template<int RADIUS>
__device__ void InitColSSD(int x_tex, int y_tex, int im_pitch, unsigned char* imageL, unsigned char* imageR, int d, volatile unsigned int *col_ssd)
{
    unsigned char leftPixel1;
    int idx;
    unsigned int diffa[] = {0, 0, 0, 0, 0, 0, 0, 0};

    for(int i = 0; i < (2 * RADIUS + 1); i++)
    {
        idx = y_tex * im_pitch + x_tex;
        leftPixel1 = imageL[idx];
        idx = idx - d;

        diffa[0] += SQ(leftPixel1 - imageR[idx - 0]);
        diffa[1] += SQ(leftPixel1 - imageR[idx - 1]);
        diffa[2] += SQ(leftPixel1 - imageR[idx - 2]);
        diffa[3] += SQ(leftPixel1 - imageR[idx - 3]);
        diffa[4] += SQ(leftPixel1 - imageR[idx - 4]);
        diffa[5] += SQ(leftPixel1 - imageR[idx - 5]);
        diffa[6] += SQ(leftPixel1 - imageR[idx - 6]);
        diffa[7] += SQ(leftPixel1 - imageR[idx - 7]);

        y_tex += 1;
    }
    //See above:  #define COL_SSD_SIZE (BLOCK_W + 2 * RADIUS)
    col_ssd[0 * (BLOCK_W + 2 * RADIUS)] = diffa[0];
    col_ssd[1 * (BLOCK_W + 2 * RADIUS)] = diffa[1];
    col_ssd[2 * (BLOCK_W + 2 * RADIUS)] = diffa[2];
    col_ssd[3 * (BLOCK_W + 2 * RADIUS)] = diffa[3];
    col_ssd[4 * (BLOCK_W + 2 * RADIUS)] = diffa[4];
    col_ssd[5 * (BLOCK_W + 2 * RADIUS)] = diffa[5];
    col_ssd[6 * (BLOCK_W + 2 * RADIUS)] = diffa[6];
    col_ssd[7 * (BLOCK_W + 2 * RADIUS)] = diffa[7];
}

template<int RADIUS>
__global__ void stereoKernel(unsigned char *left, unsigned char *right, size_t img_step, unsigned char* disp, size_t disp_pitch, int maxdisp)
{
    extern __shared__ unsigned int col_ssd_cache[];
    volatile unsigned int *col_ssd = col_ssd_cache + BLOCK_W + threadIdx.x;
    volatile unsigned int *col_ssd_extra = threadIdx.x < (2 * RADIUS) ? col_ssd + BLOCK_W : 0;  //#define N_DIRTY_PIXELS (2 * RADIUS)

    //#define X (blockIdx.x * BLOCK_W + threadIdx.x + STEREO_MAXD)
    int X = (blockIdx.x * BLOCK_W + threadIdx.x + maxdisp + RADIUS);
    //#define Y (__mul24(blockIdx.y, ROWSperTHREAD) + RADIUS)
    #define Y (blockIdx.y * ROWSperTHREAD + RADIUS)
    //int Y = blockIdx.y * ROWSperTHREAD + RADIUS;

    unsigned int* minSSDImage = cminSSDImage + X + Y * cminSSD_step;
    unsigned char* disparImage = disp + X + Y * disp_pitch;
 /*   if (X < cwidth)
    {
        unsigned int *minSSDImage_end = minSSDImage + min(ROWSperTHREAD, cheight - Y) * minssd_step;
        for(uint *ptr = minSSDImage; ptr != minSSDImage_end; ptr += minssd_step )
            *ptr = 0xFFFFFFFF;
    }*/
    int end_row = min(ROWSperTHREAD, cheight - Y);
    int y_tex;
    int x_tex = X - RADIUS;

    if (x_tex >= cwidth)
        return;

    for(int d = STEREO_MIND; d < maxdisp; d += STEREO_DISP_STEP)
    {
        y_tex = Y - RADIUS;

        InitColSSD<RADIUS>(x_tex, y_tex, img_step, left, right, d, col_ssd);

        if (col_ssd_extra > 0)
            if (x_tex + BLOCK_W < cwidth)
                InitColSSD<RADIUS>(x_tex + BLOCK_W, y_tex, img_step, left, right, d, col_ssd_extra);

        __syncthreads(); //before MinSSD function

        if (X < cwidth - RADIUS && Y < cheight - RADIUS)
        {
            uint2 minSSD = MinSSD<RADIUS>(col_ssd_cache + threadIdx.x, col_ssd);
            if (minSSD.x < minSSDImage[0])
            {
                disparImage[0] = (unsigned char)(d + minSSD.y);
                minSSDImage[0] = minSSD.x;
            }
        }

        for(int row = 1; row < end_row; row++)
        {
            int idx1 = y_tex * img_step + x_tex;
            int idx2 = (y_tex + (2 * RADIUS + 1)) * img_step + x_tex;

            __syncthreads();

            StepDown<RADIUS>(idx1, idx2, left, right, d, col_ssd);

            if (col_ssd_extra)
                if (x_tex + BLOCK_W < cwidth)
                    StepDown<RADIUS>(idx1, idx2, left + BLOCK_W, right + BLOCK_W, d, col_ssd_extra);

            y_tex += 1;

            __syncthreads(); //before MinSSD function

            if (X < cwidth - RADIUS && row < cheight - RADIUS - Y)
            {
                int idx = row * cminSSD_step;
                uint2 minSSD = MinSSD<RADIUS>(col_ssd_cache + threadIdx.x, col_ssd);
                if (minSSD.x < minSSDImage[idx])
                {
                    disparImage[disp_pitch * row] = (unsigned char)(d + minSSD.y);
                    minSSDImage[idx] = minSSD.x;
                }
            }
        } // for row loop
    } // for d loop
}

}


namespace cv { namespace gpu { namespace bm
{
    template<int RADIUS> void kernel_caller(const DevMem2D& left, const DevMem2D& right, const DevMem2D& disp, int maxdisp, const cudaStream_t & stream)
    {
        dim3 grid(1,1,1);
        dim3 threads(BLOCK_W, 1, 1);

        grid.x = divUp(left.cols - maxdisp - 2 * RADIUS, BLOCK_W);
        grid.y = divUp(left.rows - 2 * RADIUS, ROWSperTHREAD);

        //See above:  #define COL_SSD_SIZE (BLOCK_W + 2 * RADIUS)
        size_t smem_size = (BLOCK_W + N_DISPARITIES * (BLOCK_W + 2 * RADIUS)) * sizeof(unsigned int);

        if (stream == 0)
        {
            stereobm_gpu::stereoKernel<RADIUS><<<grid, threads, smem_size>>>(left.ptr, right.ptr, left.step, disp.ptr, disp.step, maxdisp);
            cudaSafeCall( cudaThreadSynchronize() );
        }
        else
        {
            stereobm_gpu::stereoKernel<RADIUS><<<grid, threads, smem_size, stream>>>(left.ptr, right.ptr, left.step, disp.ptr, disp.step, maxdisp);
        }

    };

    typedef void (*kernel_caller_t)(const DevMem2D& left, const DevMem2D& right, const DevMem2D& disp, int maxdisp, const cudaStream_t & stream);

    const static kernel_caller_t callers[] =
    {
        0,
        kernel_caller< 1>, kernel_caller< 2>, kernel_caller< 3>, kernel_caller< 4>, kernel_caller< 5>,
        kernel_caller< 6>, kernel_caller< 7>, kernel_caller< 8>, kernel_caller< 9>, kernel_caller<10>,
        kernel_caller<11>, kernel_caller<12>, kernel_caller<13>, kernel_caller<15>, kernel_caller<15>,
        kernel_caller<16>, kernel_caller<17>, kernel_caller<18>, kernel_caller<19>, kernel_caller<20>,
        kernel_caller<21>, kernel_caller<22>, kernel_caller<23>, kernel_caller<24>, kernel_caller<25>

        //0,0,0, 0,0,0, 0,0,kernel_caller<9>
    };
    const int calles_num = sizeof(callers)/sizeof(callers[0]);

    extern "C" void stereoBM_GPU(const DevMem2D& left, const DevMem2D& right, const DevMem2D& disp, int maxdisp, int winsz, const DevMem2D_<unsigned int>& minSSD_buf, const cudaStream_t & stream)
    {
        int winsz2 = winsz >> 1;

        if (winsz2 == 0 || winsz2 >= calles_num)
            cv::gpu::error("Unsupported window size", __FILE__, __LINE__);

        //cudaSafeCall( cudaFuncSetCacheConfig(&stereoKernel, cudaFuncCachePreferL1) );
        //cudaSafeCall( cudaFuncSetCacheConfig(&stereoKernel, cudaFuncCachePreferShared) );

        cudaSafeCall( cudaMemset2D(disp.ptr, disp.step, 0, disp.cols, disp.rows) );
        cudaSafeCall( cudaMemset2D(minSSD_buf.ptr, minSSD_buf.step, 0xFF, minSSD_buf.cols * minSSD_buf.elemSize(), disp.rows) );

        cudaSafeCall( cudaMemcpyToSymbol(  stereobm_gpu::cwidth, &left.cols, sizeof(left.cols) ) );
        cudaSafeCall( cudaMemcpyToSymbol( stereobm_gpu::cheight, &left.rows, sizeof(left.rows) ) );
        cudaSafeCall( cudaMemcpyToSymbol( stereobm_gpu::cminSSDImage, &minSSD_buf.ptr, sizeof(minSSD_buf.ptr) ) );

        size_t minssd_step = minSSD_buf.step/minSSD_buf.elemSize();
        cudaSafeCall( cudaMemcpyToSymbol( stereobm_gpu::cminSSD_step,  &minssd_step, sizeof(minssd_step) ) );

        callers[winsz2](left, right, disp, maxdisp, stream);
    }
}}}

//////////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////// Sobel Prefiler ///////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////////////////////

namespace stereobm_gpu
{

texture<unsigned char, 2, cudaReadModeElementType> texForSobel;

extern "C" __global__ void prefilter_kernel(unsigned char *output, size_t step, int width, int height, int prefilterCap)
{
    int x = blockDim.x * blockIdx.x + threadIdx.x;
    int y = blockDim.y * blockIdx.y + threadIdx.y;

    if (x < width && y < height)
    {
        int conv = (int)tex2D(texForSobel, x - 1, y - 1) * (-1) + (int)tex2D(texForSobel, x + 1, y - 1) * (1) +
                   (int)tex2D(texForSobel, x - 1, y    ) * (-2) + (int)tex2D(texForSobel, x + 1, y    ) * (2) +
                   (int)tex2D(texForSobel, x - 1, y + 1) * (-1) + (int)tex2D(texForSobel, x + 1, y + 1) * (1);


        conv = min(min(max(-prefilterCap, conv), prefilterCap) + prefilterCap, 255);
        output[y * step + x] = conv & 0xFF;
    }
}

}

namespace cv { namespace gpu  { namespace bm
{
    extern "C" void prefilter_xsobel(const DevMem2D& input, const DevMem2D& output, int prefilterCap, const cudaStream_t & stream)
    {
        cudaChannelFormatDesc desc = cudaCreateChannelDesc<unsigned char>();
        cudaSafeCall( cudaBindTexture2D( 0, stereobm_gpu::texForSobel, input.ptr, desc, input.cols, input.rows, input.step ) );

        dim3 threads(16, 16, 1);
        dim3 grid(1, 1, 1);

        grid.x = divUp(input.cols, threads.x);
        grid.y = divUp(input.rows, threads.y);

        if (stream == 0)
        {
			stereobm_gpu::prefilter_kernel<<<grid, threads>>>(output.ptr, output.step, output.cols, output.rows, prefilterCap);
			cudaSafeCall( cudaThreadSynchronize() );
        }
        else
        {
            stereobm_gpu::prefilter_kernel<<<grid, threads, 0, stream>>>(output.ptr, output.step, output.cols, output.rows, prefilterCap);
        }

        cudaSafeCall( cudaUnbindTexture (stereobm_gpu::texForSobel ) );

    }

}}}

//////////////////////////////////////////////////////////////////////////////////////////////////
/////////////////////////////////// Textureness filtering ////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////////////////////

namespace stereobm_gpu
{

texture<unsigned char, 2, cudaReadModeNormalizedFloat> texForTF;

__device__ float sobel(int x, int y)
{
    float conv = tex2D(texForTF, x - 1, y - 1) * (-1) + tex2D(texForTF, x + 1, y - 1) * (1) +
                 tex2D(texForTF, x - 1, y    ) * (-2) + tex2D(texForTF, x + 1, y    ) * (2) +
                 tex2D(texForTF, x - 1, y + 1) * (-1) + tex2D(texForTF, x + 1, y + 1) * (1);
    return fabs(conv);
}

__device__ float CalcSums(float *cols, float *cols_cache, int winsz)
{
    float cache = 0;
    float cache2 = 0;
    int winsz2 = winsz/2;

    for(int i = 1; i <= winsz2; i++)
        cache += cols[i];

    cols_cache[0] = cache;

    __syncthreads();

    if (threadIdx.x < blockDim.x - winsz2)
        cache2 = cols_cache[winsz2];
    else
        for(int i = winsz2 + 1; i < winsz; i++)
            cache2 += cols[i];

    return cols[0] + cache + cache2;
}

#define RpT (2 * ROWSperTHREAD)  // got experimentally

extern "C" __global__ void textureness_kernel(unsigned char *disp, size_t disp_step, int winsz, float threshold, int width, int height)
{
    int winsz2 = winsz/2;
    int n_dirty_pixels = (winsz2) * 2;

    extern __shared__ float cols_cache[];
    float *cols = cols_cache + blockDim.x + threadIdx.x;
    float *cols_extra = threadIdx.x < n_dirty_pixels ? cols + blockDim.x : 0;

    int x = blockIdx.x * blockDim.x + threadIdx.x;
    int beg_row = blockIdx.y * RpT;
    int end_row = min(beg_row + RpT, height);

    if (x < width)
    {
        int y = beg_row;

        float sum = 0;
        float sum_extra = 0;

        for(int i = y - winsz2; i <= y + winsz2; ++i)
        {
            sum += sobel(x - winsz2, i);
            if (cols_extra)
                sum_extra += sobel(x + blockDim.x - winsz2, i);
        }
        *cols = sum;
        if (cols_extra)
            *cols_extra = sum_extra;

        __syncthreads();

        float sum_win = CalcSums(cols, cols_cache + threadIdx.x, winsz) * 255;
        if (sum_win < threshold)
            disp[y * disp_step + x] = 0;

        __syncthreads();

        for(int y = beg_row + 1; y < end_row; ++y)
        {
            sum = sum - sobel(x - winsz2, y - winsz2 - 1) + sobel(x - winsz2, y + winsz2);
            *cols = sum;

            if (cols_extra)
            {
                sum_extra = sum_extra - sobel(x + blockDim.x - winsz2, y - winsz2 - 1) + sobel(x + blockDim.x - winsz2, y + winsz2);
                *cols_extra = sum_extra;
            }

            __syncthreads();
            float sum_win = CalcSums(cols, cols_cache + threadIdx.x, winsz) * 255;
            if (sum_win < threshold)
                disp[y * disp_step + x] = 0;

            __syncthreads();
        }
    }
}
}

namespace cv { namespace gpu  { namespace bm
{
    extern "C" void postfilter_textureness(const DevMem2D& input, int winsz, float avgTexturenessThreshold, const DevMem2D& disp, const cudaStream_t & stream)
    {
        avgTexturenessThreshold *= winsz * winsz;

        stereobm_gpu::texForTF.filterMode     = cudaFilterModeLinear;
        stereobm_gpu::texForTF.addressMode[0] = cudaAddressModeWrap;
        stereobm_gpu::texForTF.addressMode[1] = cudaAddressModeWrap;

        cudaChannelFormatDesc desc = cudaCreateChannelDesc<unsigned char>();
        cudaSafeCall( cudaBindTexture2D( 0, stereobm_gpu::texForTF, input.ptr, desc, input.cols, input.rows, input.step ) );

        dim3 threads(128, 1, 1);
        dim3 grid(1, 1, 1);

        grid.x = divUp(input.cols, threads.x);
        grid.y = divUp(input.rows, RpT);

        size_t smem_size = (threads.x + threads.x + (winsz/2) * 2 ) * sizeof(float);

		if (stream == 0)
		{
			stereobm_gpu::textureness_kernel<<<grid, threads, smem_size>>>(disp.ptr, disp.step, winsz, avgTexturenessThreshold, disp.cols, disp.rows);
			cudaSafeCall( cudaThreadSynchronize() );
		}
		else
		{
			stereobm_gpu::textureness_kernel<<<grid, threads, smem_size, stream>>>(disp.ptr, disp.step, winsz, avgTexturenessThreshold, disp.cols, disp.rows);		
		}

        cudaSafeCall( cudaUnbindTexture (stereobm_gpu::texForTF) );
    }
}}}